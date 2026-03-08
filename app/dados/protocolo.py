from __future__ import annotations

import hashlib
import time

TAMANHO_PROTOCOLO_PUBLICO = 12


def gerar_protocolo_apoio() -> str:
    base = str(time.time_ns()).encode("utf-8")
    return hashlib.sha256(base).hexdigest()


def abreviar_protocolo(protocolo: str, tamanho: int = TAMANHO_PROTOCOLO_PUBLICO) -> str:
    return protocolo[:tamanho]
