"""adiciona tabela usuarios

Revision ID: 2b4a1e6e5f9b
Revises: 96097c95c490
Create Date: 2026-03-07 22:20:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2b4a1e6e5f9b"
down_revision = "96097c95c490"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("senha_hash", sa.String(length=255), nullable=False),
        sa.Column("papel", sa.String(length=40), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_usuarios_email"), "usuarios", ["email"], unique=True)


def downgrade():
    op.drop_index(op.f("ix_usuarios_email"), table_name="usuarios")
    op.drop_table("usuarios")
