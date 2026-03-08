"""adiciona configuracoes de paginas gerais

Revision ID: a1b2c3d4e5f6
Revises: 9f4d6b2c1a8e
Create Date: 2026-03-08 23:58:00.000000

"""

from datetime import datetime

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "9f4d6b2c1a8e"
branch_labels = None
depends_on = None


CHAVE_WIKI_ESTATUTO = "wiki_slug_estatuto"
CHAVE_WIKI_POLITICA_PRIVACIDADE = "wiki_slug_politica_privacidade"
CHAVE_WIKI_TERMOS_USO = "wiki_slug_termos_uso"


def _upsert_wiki(conn, slug: str, titulo: str, conteudo_markdown: str) -> None:
    existe = conn.execute(sa.text("SELECT id FROM wiki_paginas WHERE slug = :slug LIMIT 1"), {"slug": slug}).fetchone()
    if existe:
        return

    agora = datetime.utcnow()
    conn.execute(
        sa.text(
            """
            INSERT INTO wiki_paginas (slug, titulo, conteudo_markdown, criado_em, atualizado_em)
            VALUES (:slug, :titulo, :conteudo_markdown, :criado_em, :atualizado_em)
            """
        ),
        {
            "slug": slug,
            "titulo": titulo,
            "conteudo_markdown": conteudo_markdown,
            "criado_em": agora,
            "atualizado_em": agora,
        },
    )


def _upsert_config(conn, chave: str, valor: str) -> None:
    existe = conn.execute(
        sa.text("SELECT id FROM configuracoes_publicas WHERE chave = :chave LIMIT 1"),
        {"chave": chave},
    ).fetchone()

    if existe:
        conn.execute(
            sa.text("UPDATE configuracoes_publicas SET valor = :valor WHERE chave = :chave"),
            {"chave": chave, "valor": valor},
        )
        return

    agora = datetime.utcnow()
    conn.execute(
        sa.text(
            """
            INSERT INTO configuracoes_publicas (chave, valor, atualizado_em)
            VALUES (:chave, :valor, :atualizado_em)
            """
        ),
        {"chave": chave, "valor": valor, "atualizado_em": agora},
    )


def upgrade():
    op.create_table(
        "configuracoes_publicas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chave", sa.String(length=120), nullable=False),
        sa.Column("valor", sa.String(length=255), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_configuracoes_publicas_chave"), "configuracoes_publicas", ["chave"], unique=True)

    conn = op.get_bind()

    _upsert_wiki(
        conn,
        slug="estatuto-base",
        titulo="Estatuto Base",
        conteudo_markdown="# Estatuto Base\n\nVersao de referencia do estatuto da campanha.",
    )
    _upsert_wiki(
        conn,
        slug="politica-de-privacidade",
        titulo="Politica de Privacidade",
        conteudo_markdown="# Politica de Privacidade\n\nDocumento de referencia sobre dados e privacidade.",
    )
    _upsert_wiki(
        conn,
        slug="termos-de-uso",
        titulo="Termos de Uso",
        conteudo_markdown="# Termos de Uso\n\nDocumento de referencia sobre regras de uso da plataforma.",
    )

    _upsert_config(conn, CHAVE_WIKI_ESTATUTO, "estatuto-base")
    _upsert_config(conn, CHAVE_WIKI_POLITICA_PRIVACIDADE, "politica-de-privacidade")
    _upsert_config(conn, CHAVE_WIKI_TERMOS_USO, "termos-de-uso")


def downgrade():
    conn = op.get_bind()

    conn.execute(
        sa.text(
            "DELETE FROM configuracoes_publicas WHERE chave IN (:c1, :c2, :c3)"
        ),
        {
            "c1": CHAVE_WIKI_ESTATUTO,
            "c2": CHAVE_WIKI_POLITICA_PRIVACIDADE,
            "c3": CHAVE_WIKI_TERMOS_USO,
        },
    )

    op.drop_index(op.f("ix_configuracoes_publicas_chave"), table_name="configuracoes_publicas")
    op.drop_table("configuracoes_publicas")
