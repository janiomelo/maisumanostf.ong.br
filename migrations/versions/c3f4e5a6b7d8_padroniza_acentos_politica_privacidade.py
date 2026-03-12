"""padroniza acentos em politica de privacidade

Revision ID: c3f4e5a6b7d8
Revises: a1b2c3d4e5f6
Create Date: 2026-03-12 00:00:00.000000

"""

from datetime import datetime

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c3f4e5a6b7d8"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    agora = datetime.utcnow()
    conn.execute(
        sa.text(
            """
            UPDATE wiki_paginas
            SET titulo = :titulo,
                conteudo_markdown = REPLACE(conteudo_markdown, :de, :para),
                atualizado_em = :atualizado_em
            WHERE slug = :slug
            """
        ),
        {
            "titulo": "Política de Privacidade",
            "de": "# Politica de Privacidade",
            "para": "# Política de Privacidade",
            "atualizado_em": agora,
            "slug": "politica-de-privacidade",
        },
    )


def downgrade():
    conn = op.get_bind()
    agora = datetime.utcnow()
    conn.execute(
        sa.text(
            """
            UPDATE wiki_paginas
            SET titulo = :titulo,
                conteudo_markdown = REPLACE(conteudo_markdown, :de, :para),
                atualizado_em = :atualizado_em
            WHERE slug = :slug
            """
        ),
        {
            "titulo": "Politica de Privacidade",
            "de": "# Política de Privacidade",
            "para": "# Politica de Privacidade",
            "atualizado_em": agora,
            "slug": "politica-de-privacidade",
        },
    )
