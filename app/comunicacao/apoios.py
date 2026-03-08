from __future__ import annotations

from collections.abc import Mapping

from flask import render_template

from .resend import enviar_email_resend

ASSUNTO_CONFIRMACAO_APOIO = "Confirmação de apoio ao manifesto | Mais Uma no STF"


def enviar_email_confirmacao_apoio(
    *,
    config: Mapping[str, object],
    destinatario: str,
    nome_publico: str,
    ordem_apoio: int,
    url_site: str,
) -> str | None:
    api_key = str(config.get("RESEND_API_KEY", "") or "").strip()
    remetente = str(config.get("RESEND_FROM_EMAIL", "") or "").strip()
    if not api_key or not remetente:
        return None

    canal_contato = str(config.get("APOIOS_EMAIL_CONTATO", "") or "").strip() or remetente
    reply_to = str(config.get("RESEND_REPLY_TO", "") or "").strip() or None
    site_publico = str(config.get("SITE_URL", "") or "").strip() or url_site.rstrip("/")

    html = montar_html_confirmacao_apoio(
        destinatario=destinatario,
        nome_publico=nome_publico,
        ordem_apoio=ordem_apoio,
        canal_contato=canal_contato,
        site_publico=site_publico,
    )

    return enviar_email_resend(
        api_key=api_key,
        remetente=remetente,
        destinatario=destinatario,
        assunto=ASSUNTO_CONFIRMACAO_APOIO,
        html=html,
        reply_to=reply_to,
    )


def montar_html_confirmacao_apoio(
    *,
    destinatario: str,
    nome_publico: str,
    ordem_apoio: int,
    canal_contato: str,
    site_publico: str,
) -> str:
    nome_publico_formatado = nome_publico.strip() or "não informado"
    url_apoios = f"{site_publico.rstrip('/')}/apoios/assinar"

    return render_template(
        "emails/confirmacao-apoio.html",
        destinatario=destinatario,
        nome_publico=nome_publico_formatado,
        ordem_apoio=ordem_apoio,
        canal_contato=canal_contato,
        url_apoios=url_apoios,
    )
