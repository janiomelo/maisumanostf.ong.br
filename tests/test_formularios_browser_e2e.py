import socket
import threading
from contextlib import closing

import pytest
from werkzeug.serving import make_server



def _porta_livre() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        return int(sock.getsockname()[1])


@pytest.fixture
def servidor_http_local(app_instance):
    porta = _porta_livre()
    servidor = make_server("127.0.0.1", porta, app_instance)
    thread = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread.start()

    try:
        yield f"http://127.0.0.1:{porta}"
    finally:
        servidor.shutdown()
        thread.join(timeout=2)


@pytest.mark.e2e
def test_formularios_login_e_wiki_funcionam_no_navegador(servidor_http_local):
    playwright_api = pytest.importorskip("playwright.sync_api")

    try:
        with playwright_api.sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(f"{servidor_http_local}/entrar", wait_until="networkidle")
            page.fill("#email", "editor@teste.local")
            page.fill("#senha", "123456")
            page.locator("form[action$='/entrar'] button[type='submit']").click()

            page.wait_for_url("**/wiki/")
            assert "Wiki da Campanha" in page.content()

            page.goto(f"{servidor_http_local}/wiki/nova", wait_until="networkidle")
            page.fill("#titulo", "Pagina Criada via Browser E2E")
            page.fill("#slug", "pagina-criada-via-browser-e2e")

            # EasyMDE usa CodeMirror; o input real ocorre no editor renderizado.
            page.click(".CodeMirror")
            page.keyboard.type("# Pagina Criada via Browser E2E\n\nConteudo enviado pelo navegador.")
            page.locator("form[action$='/wiki/nova'] button[type='submit']").click()

            page.wait_for_url("**/wiki/pagina-criada-via-browser-e2e")
            html = page.content()
            assert "Pagina Criada via Browser E2E" in html
            assert "Conteudo enviado pelo navegador." in html

            browser.close()
    except Exception as exc:  # pragma: no cover
        msg = str(exc).lower()
        if "executable doesn't exist" in msg or "browser" in msg and "install" in msg:
            pytest.skip("Chromium do Playwright nao encontrado. Rode: playwright install chromium")
        if "error while loading shared libraries" in msg or "libglib" in msg:
            pytest.skip("Runtime do Chromium indisponivel no container (libs de sistema ausentes)")
        raise
