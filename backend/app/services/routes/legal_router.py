from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

_PAGES = Path(__file__).resolve().parent / "legal_pages"

_DELETE_ACCOUNT = """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Exclusão de conta | CryptoRadar</title>
<style>body{font:16px/1.65 system-ui,sans-serif;color:#17283a;background:#f3f6fa;margin:0}main{max-width:820px;margin:24px auto;padding:clamp(18px,5vw,42px);background:white;border-radius:12px}a{color:#145ca5}</style>
</head><body><main><strong>CryptoRadar</strong>
<h1>Solicitar exclusão de conta e dados</h1>
<p>Este procedimento destina-se à conta CryptoRadar, não à sua conta Google.</p>
<ol><li>Envie um e-mail para <a href="mailto:cryptoradar.app@gmail.com?subject=Exclus%C3%A3o%20de%20conta%20CryptoRadar">cryptoradar.app@gmail.com</a> com o assunto Exclusão de conta CryptoRadar.</li>
<li>Use, se possível, o e-mail vinculado à sua conta. Não envie senhas, códigos de autenticação nem tokens de compra.</li>
<li>O suporte poderá confirmar sua identidade e informar o andamento da solicitação.</li></ol>
<h2>Dados abrangidos</h2><p>A solicitação abrange a conta CryptoRadar e os dados pessoais associados, incluindo identificadores de instalação, preferências de monitoramento e notificações. Registros que precisem ser conservados por obrigações legais ou razões legítimas de segurança poderão ser retidos pelo período necessário, com informação sobre a justificativa aplicável.</p>
<h2>Assinaturas</h2><p>Excluir a conta não cancela automaticamente a assinatura. Gerencie ou cancele sua assinatura em <a href="https://play.google.com/store/account/subscriptions">Assinaturas do Google Play</a>.</p>
<p>Esta página inicia uma solicitação ao suporte; não realiza a exclusão automaticamente.</p>
<p><a href="/privacy">Política de Privacidade</a> · <a href="/terms">Termos de Uso</a></p>
</main></body></html>"""


def create_legal_router() -> APIRouter:
    router = APIRouter(tags=["legal"])

    @router.get("/privacy", response_class=HTMLResponse)
    def privacy():
        return HTMLResponse((_PAGES / "privacidade.html").read_text(encoding="utf-8"))

    @router.get("/terms", response_class=HTMLResponse)
    def terms():
        return HTMLResponse((_PAGES / "termos.html").read_text(encoding="utf-8"))

    @router.get("/delete-account", response_class=HTMLResponse)
    def delete_account():
        return HTMLResponse(_DELETE_ACCOUNT)

    return router
