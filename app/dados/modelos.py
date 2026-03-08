from datetime import UTC, datetime

from werkzeug.security import check_password_hash, generate_password_hash

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


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    papel = db.Column(db.String(40), nullable=False, default="nao_editor")
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    origem_auth = db.Column(db.String(20), nullable=False, default="local")
    google_sub = db.Column(db.String(255), unique=True, nullable=True, index=True)
    email_verificado = db.Column(db.Boolean, nullable=False, default=False)

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

    def definir_senha(self, senha_plana: str) -> None:
        self.senha_hash = generate_password_hash(senha_plana)

    def validar_senha(self, senha_plana: str) -> bool:
        return check_password_hash(self.senha_hash, senha_plana)


class ApoioManifesto(db.Model):
    __tablename__ = "apoios_manifesto"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    nome = db.Column(db.String(255), nullable=False)

    @staticmethod
    def _agora_utc() -> datetime:
        return datetime.now(UTC)

    criado_em = db.Column(db.DateTime, nullable=False, default=_agora_utc)
