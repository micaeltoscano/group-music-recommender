# Documentação — Vibe Check

Índice de navegação. **Comece por aqui** se estiver perdido.

## 🚀 Por onde começar

| Você quer… | Vá para |
|---|---|
| Entender o produto e os critérios de aceitação | [`produto/BACKLOG_PRODUTO.md`](produto/BACKLOG_PRODUTO.md) |
| Saber a Sprint ativa, o próximo PB e o status de tudo | [`planejamento/PLANO_EXECUCAO.md`](planejamento/PLANO_EXECUCAO.md) |
| Ver **quem faz o quê** (divisão eu × colega) | [`planejamento/MAPA_TRABALHO.md`](planejamento/MAPA_TRABALHO.md) |
| Saber como cada PB é testado | [`planejamento/PLANO_TESTES.md`](planejamento/PLANO_TESTES.md) |
| Recriar as telas do frontend | [`design/README.md`](design/README.md) |

## 📁 Estrutura

```
docs/
├── produto/            O QUÊ construir
│   ├── BACKLOG_PRODUTO.md      ← escopo, histórias, critérios de aceitação (fonte de verdade)
│   └── _originais/             ← exports originais do backlog (referência, não editar)
│
├── planejamento/       QUANDO e por QUEM
│   ├── PLANO_EXECUCAO.md       ← memória operacional: Sprint ativa, status por PB, retomada
│   ├── PLANO_TESTES.md         ← casos de teste (CT-*) por PB e por Sprint
│   └── MAPA_TRABALHO.md        ← dependências + divisão 50/50 por Sprint (eu × colega)
│
├── agentes/            COMO os agentes trabalham
│   ├── PROTOCOLO.md            ← contrato Dev↔QA, sinais de handoff, portão de espera
│   ├── AGENTE_IMPLEMENTACAO.md ← prompt do papel de implementação
│   └── AGENTE_TESTE.md         ← prompt do papel de QA
│
├── design/             COMO deve parecer
│   ├── README.md              ← handoff (tokens de cor/tipografia, telas)
│   ├── vibe-check-prototype.html   ← protótipo interativo (referência visual, não copiar)
│   └── screenshots/           ← 01-login … 07-feedback
│
└── relatorios-testes/  RESULTADO da validação
    └── PB-XX.md               ← veredito do QA + defeitos por PB
```

## 🤖 Arquivos de agente (na raiz do repositório)

Cada ferramenta de IA lê o seu automaticamente:

- [`../AGENTS.md`](../AGENTS.md) — **Codex / Cursor** (implementação — Micael)
- [`../CLAUDE.md`](../CLAUDE.md) — **Claude** (QA — Micael)
- [`../GEMINI.md`](../GEMINI.md) — **Gemini** (implementação + QA — colega)

## ▶️ Rodar o ciclo de agentes

```bash
./scripts/orquestrar.sh --profile claude-codex   # Micael: Codex implementa, Claude valida
./scripts/orquestrar.sh --profile gemini          # colega: Gemini nas duas fases
./scripts/orquestrar.sh --profile gemini --dry-run   # simular sem chamar IA nem alterar arquivos
```

Detalhes do orquestrador: cabeçalho de [`../scripts/orquestrar.sh`](../scripts/orquestrar.sh).
