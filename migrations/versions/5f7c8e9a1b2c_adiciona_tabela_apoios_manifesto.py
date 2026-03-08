"""adiciona tabela apoios_manifesto

Revision ID: 5f7c8e9a1b2c
Revises: 2b4a1e6e5f9b
Create Date: 2026-03-08 17:30:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "5f7c8e9a1b2c"
down_revision = "2b4a1e6e5f9b"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "apoios_manifesto",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_apoios_manifesto_email"), "apoios_manifesto", ["email"], unique=True)


def downgrade():
    op.drop_index(op.f("ix_apoios_manifesto_email"), table_name="apoios_manifesto")
    op.drop_table("apoios_manifesto")
