from __future__ import annotations

from typing import Any

import requests


class ErroClienteResend(RuntimeError):
    pass


def enviar_email_resend(
    *,
    api_key: str,
    remetente: str,
    destinatario: str,
    assunto: str,
    html: str,
    reply_to: str | None = None,
    timeout_segundos: int = 10,
) -> str:
    if not api_key.strip():
        raise ValueError("RESEND_API_KEY e obrigatoria")
    if not remetente.strip():
        raise ValueError("RESEND_FROM_EMAIL e obrigatorio")
    if not destinatario.strip():
        raise ValueError("Destinatario e obrigatorio")

    payload: dict[str, Any] = {
        "from": remetente,
        "to": [destinatario],
        "subject": assunto,
        "html": html,
    }
    if reply_to:
        payload["reply_to"] = reply_to

    response = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=timeout_segundos,
    )

    if response.status_code >= 400:
        raise ErroClienteResend(_extrair_erro(response))

    corpo = response.json()
    mensagem_id = str(corpo.get("id", "")).strip()
    if not mensagem_id:
        raise ErroClienteResend("Resend retornou sucesso sem id de mensagem")

    return mensagem_id


def _extrair_erro(response: requests.Response) -> str:
    try:
        corpo = response.json()
    except ValueError:
        return f"Falha ao enviar via Resend (status {response.status_code})"

    erro = corpo.get("message") or corpo.get("error")
    if isinstance(erro, str) and erro.strip():
        return erro.strip()

    return f"Falha ao enviar via Resend (status {response.status_code})"
