"""PB-35 — contrato frontend do logout visível na Home."""

from pathlib import Path


ROOT = Path(__file__).parents[2]


def _source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_ct_pb35_01_acao_acessivel_no_cabecalho():
    home = _source("frontend/src/Home.jsx")
    assert 'className="home-header-actions"' in home
    assert 'className="home-logout-button"' in home
    assert 'type="button"' in home
    assert "SAIR" in home


def test_ct_pb35_02_usa_post_logout_e_nao_exclusao():
    api = _source("frontend/src/apiClient.js")
    assert "logout: () => requestJson('/auth/logout', { method: 'POST' })" in api
    assert "delete" not in api.split("logout:", 1)[1].splitlines()[0].lower()


def test_ct_pb35_03_sucesso_limpa_usuario_e_retorna_login():
    app = _source("frontend/src/App.jsx")
    home = _source("frontend/src/Home.jsx")
    assert "onLogout={() => setUser(null)}" in app
    assert "onLogout()" in home
    assert '<Navigate to="/login" replace />' in app


def test_ct_pb35_04_falha_mantem_sessao_e_reabilita_acao():
    home = _source("frontend/src/Home.jsx")
    assert "Sua sessão continua ativa" in home
    assert "setLogoutError" in home
    assert "finally" in home and "setLoggingOut(false)" in home
    assert "onLogout()" not in home.split("catch", 1)[1].split("finally", 1)[0]


def test_ct_pb35_05_loading_responsividade_e_regressao_visual():
    home = _source("frontend/src/Home.jsx")
    css = _source("frontend/src/index.css")
    assert "loggingOut ? 'SAINDO…' : 'SAIR'" in home
    assert "disabled={loggingOut}" in home
    assert ".home-logout-button:focus-visible" in css
    assert "@media (max-width: 640px)" in css
    assert ".home-header-actions > .eyebrow" in css
    assert "createRoom" in home and "joinRoom" in home and "refreshLibrary" in home
