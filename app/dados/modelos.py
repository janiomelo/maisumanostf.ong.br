from datetime import UTC, datetime

from .base import db


class WikiPagina(db.Model):
    __tablename__ = "wiki_paginas"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(120), unique=True, nullable=False, index=True)
    titulo = db.Column(db.String(255), nullable=False)
    conteudo_markdown = db.Column(db.Text, nullable=False)

    @staticmethod
    def _agora_utc() -> datetime:
        return datetime.now(UTC)

    criado_em = db.Column(db.DateTime, nullable=False, default=_agora_utc)
    atualizado_em = db.Column(
        db.DateTime,
        nullable=False,
        default=_agora_utc,
        onupdate=_agora_utc,
    )
