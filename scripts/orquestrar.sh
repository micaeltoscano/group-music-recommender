#!/usr/bin/env bash
#
# orquestrar.sh — Orquestração Dev (Codex) ↔ QA (Claude) para o Vibe Check.
#
# O que faz:
#   1. Sincroniza o repositório (git pull) para enxergar o trabalho do colega.
#   2. Descobre SOZINHO o próximo PB acionável, lendo o campo `Status` de cada PB
#      no PLANO_EXECUCAO.md, na ordem da Sprint ativa (linha "Em andamento" da tabela).
#   3. Roda a fase certa conforme o Status:
#        A-FAZER / EM-IMPLEMENTACAO -> Implementação (Codex) + QA (Claude)
#        AGUARDANDO-QA              -> só QA (Claude)          <- trabalho do colega
#        REPROVADO                  -> Implementação (correção) + QA
#        VALIDADO                   -> pula
#        BLOQUEADO                  -> pula com aviso
#   4. Carimba o Status de volta no plano conforme a assinatura emitida pelo agente.
#   5. No modo --passo (padrão), pergunta antes de seguir para o próximo PB.
#
# Uso (trabalho em dupla — cada um escolhe seus PBs, sem ordem fixa):
#   scripts/orquestrar.sh --list                     # panorama: o que está livre/em andamento/feito
#   scripts/orquestrar.sh --pb PB-04                  # faz o ciclo de UM PB (reivindica o dono)
#   scripts/orquestrar.sh --pb PB-04 --profile gemini # colega faz o dele com Gemini
#   scripts/orquestrar.sh --pb PB-04 --force          # assume um PB já reivindicado por outro
#
# Uso (solo — percorre a Sprint automaticamente):
#   scripts/orquestrar.sh --profile claude-codex     # padrão: Codex implementa, Claude valida
#   scripts/orquestrar.sh --auto                      # roda a Sprint inteira sem perguntar
#   scripts/orquestrar.sh --dry-run                   # não chama IA; simula avançando os PBs
#   scripts/orquestrar.sh --no-pull                   # não faz git pull
#
# O perfil define as ferramentas (scripts/profiles/<perfil>.env). Também dá para sobrepor por env:
#   CODEX_CMD="codex exec"   CLAUDE_CMD="claude -p"   scripts/orquestrar.sh
#
set -uo pipefail

# --- Configuração ------------------------------------------------------------
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLANO="$ROOT/docs/planejamento/PLANO_EXECUCAO.md"
IMPL_PROMPT="$ROOT/docs/agentes/AGENTE_IMPLEMENTACAO.md"
QA_PROMPT="$ROOT/docs/agentes/AGENTE_TESTE.md"

MAX_RETRIES="${MAX_RETRIES:-2}"          # tentativas de correção por PB no modo --auto

MODO=passo; DRY_RUN=0; NOPULL=0; PROFILE="${PROFILE:-claude-codex}"
TARGET_PB=""; FORCE=0; LIST=0; OWNER="${OWNER:-}"
args=("$@"); i=0
while [ $i -lt ${#args[@]} ]; do a="${args[$i]}"; case "$a" in
  --auto)      MODO=auto ;;
  --passo)     MODO=passo ;;
  --dry-run)   DRY_RUN=1 ;;
  --no-pull)   NOPULL=1 ;;
  --force)     FORCE=1 ;;
  --list)      LIST=1 ;;
  --pb)        i=$((i+1)); TARGET_PB="${args[$i]}" ;;
  --pb=*)      TARGET_PB="${a#*=}" ;;
  --owner)     i=$((i+1)); OWNER="${args[$i]}" ;;
  --owner=*)   OWNER="${a#*=}" ;;
  --profile)   i=$((i+1)); PROFILE="${args[$i]}" ;;
  --profile=*) PROFILE="${a#*=}" ;;
  -h|--help)   grep -E '^#( |$)' "$0" | sed -E 's/^# ?//'; exit 0 ;;
  *) echo "Argumento desconhecido: $a (use --help)"; exit 2 ;;
esac; i=$((i+1)); done

# Perfil = quais ferramentas (Codex/Claude vs Gemini) rodam impl e QA.
PROFILE_FILE="$ROOT/scripts/profiles/$PROFILE.env"
if [ -f "$PROFILE_FILE" ]; then
  # shellcheck disable=SC1090
  . "$PROFILE_FILE"
else
  echo "❌ Perfil '$PROFILE' não encontrado em scripts/profiles/. Perfis disponíveis:"
  ls -1 "$ROOT/scripts/profiles/" 2>/dev/null | sed -E 's/\.env$//; s/^/   - /'
  exit 1
fi
CODEX_CMD="${CODEX_CMD:-codex exec}"     # agente de implementação (definido pelo perfil)
CLAUDE_CMD="${CLAUDE_CMD:-claude -p}"    # agente de teste (definido pelo perfil)
OWNER="${OWNER:-$(git -C "$ROOT" config user.name 2>/dev/null | tr -d ' ')}"; OWNER="${OWNER:-user}"
echo "👤 Perfil: $PROFILE ($OWNER)  ·  impl=[$CODEX_CMD]  qa=[$CLAUDE_CMD]"

[ -f "$PLANO" ] || { echo "❌ Não encontrei $PLANO"; exit 1; }

# No dry-run trabalhamos numa cópia temporária: o plano real nunca é alterado.
if [ "$DRY_RUN" = 1 ]; then
  _DRYPLANO="$(mktemp)"; cp "$PLANO" "$_DRYPLANO"; PLANO="$_DRYPLANO"
  trap 'rm -f "$_DRYPLANO"' EXIT
  echo "🧪 [dry-run] simulando sobre cópia temporária — o PLANO_EXECUCAO.md real NÃO será tocado."
fi

# --- Leitura do plano (funções puras de parsing) -----------------------------

# PBs da Sprint ativa, na ordem da tabela (linha marcada "Em andamento").
sprint_pbs() { grep -E '^\| *Sprint .*Em andamento' "$PLANO" | head -1 | grep -oE 'PB-[0-9]+'; }

# Token de Status (primeira palavra) do bloco "#### PB-XX".
status_pb() {
  awk -v pb="$1" '
    index($0,"#### " pb)==1 {inblock=1; next}
    inblock && index($0,"#### PB-")==1 {exit}
    inblock && index($0,"**Status:**")>0 && index($0,"Status (detalhe)")==0 {print; exit}
  ' "$PLANO" | sed -E 's/.*\*\*Status:\*\*[[:space:]]*([A-Za-z-]+).*/\1/'
}

# Dependências (ids PB-NN) declaradas no bloco do PB.
deps_pb() {
  awk -v pb="$1" '
    index($0,"#### " pb)==1 {inblock=1; next}
    inblock && index($0,"#### PB-")==1 {exit}
    inblock && index($0,"**Dependências:**")>0 {print; exit}
  ' "$PLANO" | grep -oE 'PB-[0-9]+'
}

# Dono do PB: extrai "@nome" do detalhe do campo Status (vazio se não houver).
owner_pb() {
  awk -v pb="$1" '
    index($0,"#### " pb)==1 {inblock=1; next}
    inblock && index($0,"#### PB-")==1 {exit}
    inblock && index($0,"**Status:**")>0 && index($0,"Status (detalhe)")==0 {print; exit}
  ' "$PLANO" | grep -oE '@[A-Za-z0-9._-]+' | head -1
}

# set_status PB TOKEN [DETALHE]. Sem DETALHE, preserva o texto após " — ".
set_status() {
  local pb="$1" tok="$2" det="${3-}" hasdet="${3+1}" tmp; tmp="$(mktemp)"
  awk -v pb="$pb" -v tok="$tok" -v det="$det" -v hasdet="$hasdet" '
    index($0,"#### " pb)==1 {inblock=1}
    inblock && !done && index($0,"**Status:**")>0 && index($0,"Status (detalhe)")==0 {
      p = index($0,"**Status:**")
      pre  = substr($0,1,p+10)          # "... - **Status:**"
      rest = substr($0,p+11)            # " TOKEN — detalhe"
      sub(/^[[:space:]]+/,"",rest)
      sub(/^[A-Za-z-]+/,"",rest)        # remove token antigo, mantém " — detalhe"
      if (hasdet=="1") print pre " " tok " — " det
      else             print pre " " tok rest
      done=1; next
    }
    inblock && index($0,"#### PB-")==1 && $0 !~ ("#### " pb) {inblock=0}
    {print}
  ' "$PLANO" > "$tmp" && mv "$tmp" "$PLANO"
  echo "   ✎ Status de $pb → $tok"
}

# Reivindica o PB para o dono atual (marca EM-IMPLEMENTACAO — @dono).
claim() { set_status "$1" EM-IMPLEMENTACAO "@$OWNER (desde $(date +%F))"; }

# Panorama da Sprint ativa: status, situação e dono de cada PB.
overview() {
  echo "🎯 Sprint ativa — situação dos PBs:"
  local pb st dn dep d sit
  for pb in $(sprint_pbs); do
    st="$(status_pb "$pb")"; dn="$(owner_pb "$pb")"; dep=""
    for d in $(deps_pb "$pb"); do [ "$(status_pb "$d")" != VALIDADO ] && dep="$dep $d"; done
    case "$st" in
      A-FAZER)          [ -n "$dep" ] && sit="🔒 espera:$dep" || sit="🟢 LIVRE" ;;
      EM-IMPLEMENTACAO) sit="🛠  em implementação" ;;
      AGUARDANDO-QA)    sit="🧪 aguardando QA" ;;
      REPROVADO)        sit="🔁 reprovado" ;;
      VALIDADO)         sit="✅ feito" ;;
      *)                sit="? ($st)" ;;
    esac
    printf "   %-7s %-16s %-22s %s\n" "$pb" "$st" "$sit" "$dn"
  done
}

# Primeiro PB acionável na ordem da Sprint (pula VALIDADO/BLOQUEADO).
proximo_pb() {
  local pb st
  for pb in $(sprint_pbs); do
    st="$(status_pb "$pb")"
    case "$st" in
      VALIDADO)  continue ;;
      BLOQUEADO) echo "   ⏭  $pb BLOQUEADO — pulando (verifique dependências/bloqueio externo)" >&2; continue ;;
      A-FAZER|EM-IMPLEMENTACAO|AGUARDANDO-QA|REPROVADO) echo "$pb"; return 0 ;;
      *) echo "   ⚠  $pb com Status não reconhecido: '$st' — pulando" >&2; continue ;;
    esac
  done
  return 1
}

deps_ok() {
  local pb="$1" d st ok=0
  for d in $(deps_pb "$pb"); do
    st="$(status_pb "$d")"
    if [ "$st" != VALIDADO ]; then
      echo "   ↳ dependência $d está '$st' (precisa VALIDADO)" >&2; ok=1
    fi
  done
  return $ok
}

# --- Fases (chamada aos agentes) ---------------------------------------------

fase_impl() {
  local pb="$1" ctx out
  echo "🛠  Implementação [$CODEX_CMD] — $pb"
  ctx="$(cat "$IMPL_PROMPT")

## Instrução do orquestrador (complementa o prompt acima)
- PB ativo AGORA: $pb. Implemente SOMENTE $pb (código + testes).
- Ao concluir: no PLANO_EXECUCAO.md, marque o Status de $pb como AGUARDANDO-QA, faça commit do PB e
  emita LITERALMENTE '$pb IMPLEMENTADO — INICIANDO VALIDAÇÃO'. Depois pare."
  if [ "$DRY_RUN" = 1 ]; then
    echo "   [dry-run] $CODEX_CMD \"<AGENTE_IMPLEMENTACAO + contexto $pb>\""
    set_status "$pb" AGUARDANDO-QA; return 0
  fi
  out="$($CODEX_CMD "$ctx" 2>&1 | tee /dev/tty)"
  echo "$out" | grep -q "$pb IMPLEMENTADO" || return 1
  set_status "$pb" AGUARDANDO-QA
}

fase_qa() {
  local pb="$1" ctx out
  echo "🧪 Validação [$CLAUDE_CMD] — $pb"
  ctx="$(cat "$QA_PROMPT")

## Instrução do orquestrador (complementa o prompt acima)
- Gatilho: '$pb IMPLEMENTADO — INICIANDO VALIDAÇÃO'. Valide SOMENTE $pb.
- Ao final: escreva docs/relatorios-testes/$pb.md, marque o Status de $pb como VALIDADO ou REPROVADO
  no PLANO_EXECUCAO.md, e emita LITERALMENTE a assinatura oficial correspondente."
  if [ "$DRY_RUN" = 1 ]; then
    echo "   [dry-run] $CLAUDE_CMD \"<AGENTE_TESTE + contexto $pb>\""
    set_status "$pb" VALIDADO; return 0
  fi
  out="$($CLAUDE_CMD "$ctx" 2>&1 | tee /dev/tty)"
  if   echo "$out" | grep -q "$pb VALIDADO";  then set_status "$pb" VALIDADO
  elif echo "$out" | grep -q "$pb REPROVADO"; then set_status "$pb" REPROVADO
  elif echo "$out" | grep -q "$pb BLOQUEADO"; then set_status "$pb" BLOQUEADO
  else echo "   ⚠ QA não emitiu assinatura reconhecível; mantendo Status atual."
  fi
}

# --- Pré-checagens de ambiente ----------------------------------------------
if [ "$DRY_RUN" = 0 ] && [ "$LIST" = 0 ]; then
  for c in "${CODEX_CMD%% *}" "${CLAUDE_CMD%% *}"; do
    command -v "$c" >/dev/null 2>&1 || echo "⚠ '$c' não está no PATH — use --dry-run ou ajuste CODEX_CMD/CLAUDE_CMD."
  done
fi

# --- Sincronização com o repositório ----------------------------------------
if [ "$NOPULL" = 0 ]; then
  echo "⤵  Sincronizando com o repositório (git pull)…"
  git -C "$ROOT" fetch --quiet 2>/dev/null \
    && git -C "$ROOT" pull --ff-only --quiet 2>/dev/null \
    && echo "   ✓ atualizado" \
    || echo "   ⚠ git pull não realizado (sem upstream/conflito?) — seguindo com o estado local."
fi

# --- Modo panorama (--list): mostra a situação da Sprint e sai --------------
if [ "$LIST" = 1 ]; then overview; exit 0; fi

# --- Modo PB específico (--pb PB-XX): roda o ciclo de UM PB e sai ------------
# É o modo do trabalho em dupla: cada um escolhe seus PBs e reivindica o dono.
if [ -n "$TARGET_PB" ]; then
  ST="$(status_pb "$TARGET_PB")"
  [ -z "$ST" ] && { echo "❌ $TARGET_PB não está na Sprint ativa (ou não existe)."; exit 1; }
  DONO="$(owner_pb "$TARGET_PB")"
  echo "▶  $TARGET_PB  (Status: $ST${DONO:+ · dono: $DONO})"
  if [ "$ST" = VALIDADO ]; then echo "✅ Já está VALIDADO. Nada a fazer."; exit 0; fi
  if [ -n "$DONO" ] && [ "$DONO" != "@$OWNER" ] && [ "$FORCE" = 0 ]; then
    echo "⛔ $TARGET_PB já está com $DONO. Combine com a pessoa ou use --force para assumir."; exit 1
  fi
  if ! deps_ok "$TARGET_PB"; then echo "⛔ Dependências de $TARGET_PB não estão VALIDADO. Não dá para começar ainda."; exit 1; fi
  case "$ST" in
    A-FAZER)                    claim "$TARGET_PB"; fase_impl "$TARGET_PB" && fase_qa "$TARGET_PB" ;;
    EM-IMPLEMENTACAO|REPROVADO) fase_impl "$TARGET_PB" && fase_qa "$TARGET_PB" ;;
    AGUARDANDO-QA)              fase_qa "$TARGET_PB" ;;
  esac
  echo; echo "🏁 $TARGET_PB terminou como: $(status_pb "$TARGET_PB")"
  exit 0
fi

# --- Laço principal (modo solo: percorre a Sprint automaticamente) -----------
STOPPED=0; RETRY_PB=""; RETRY_N=0
echo "🎯 Sprint ativa: PBs = $(sprint_pbs | tr '\n' ' ')"
echo

while PB="$(proximo_pb)"; do
  ST="$(status_pb "$PB")"
  echo "▶  Próximo PB: $PB  (Status: $ST)"

  if ! deps_ok "$PB"; then
    echo "⛔ Dependências de $PB não estão VALIDADO. Parando para revisão humana."
    STOPPED=1; break
  fi

  case "$ST" in
    A-FAZER|EM-IMPLEMENTACAO)
      [ "$ST" = A-FAZER ] && claim "$PB"
      fase_impl "$PB" || { echo "⛔ Implementação de $PB não sinalizou IMPLEMENTADO. Parando."; STOPPED=1; break; }
      fase_qa "$PB" ;;
    REPROVADO)
      if [ "$PB" = "$RETRY_PB" ]; then RETRY_N=$((RETRY_N + 1)); else RETRY_PB="$PB"; RETRY_N=1; fi
      if [ "$MODO" = auto ] && [ "$RETRY_N" -gt "$MAX_RETRIES" ]; then
        echo "⛔ $PB excedeu $MAX_RETRIES tentativas de correção. Parando."; STOPPED=1; break
      fi
      fase_impl "$PB" || { echo "⛔ Correção de $PB não sinalizou IMPLEMENTADO. Parando."; STOPPED=1; break; }
      fase_qa "$PB" ;;
    AGUARDANDO-QA)
      fase_qa "$PB" ;;
  esac

  NOVO="$(status_pb "$PB")"
  if [ "$NOVO" = VALIDADO ]; then
    echo "✅ $PB VALIDADO."
    if [ "$MODO" = passo ]; then
      read -r -p "➡️  Continuar para o próximo PB? [s/N] " r </dev/tty
      case "$r" in s|S) : ;; *) echo "Encerrando a pedido."; STOPPED=1; break ;; esac
    fi
  else
    echo "🔁 $PB terminou como '$NOVO' (não VALIDADO)."
    if [ "$MODO" = passo ]; then
      read -r -p "🔧 Corrigir/revalidar $PB agora? [s/N] " r </dev/tty
      case "$r" in s|S) : ;; *) echo "Parando."; STOPPED=1; break ;; esac
    fi
  fi
  echo
done

if [ "$STOPPED" = 0 ]; then
  echo "🏁 Nenhum PB pendente na Sprint ativa — pronto para a validação integrada da Sprint."
fi
