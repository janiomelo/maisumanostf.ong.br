"""adiciona campos google oauth em usuarios

Revision ID: 8c1d2e3f4a5b
Revises: 5f7c8e9a1b2c
Create Date: 2026-03-08 19:20:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8c1d2e3f4a5b"
down_revision = "5f7c8e9a1b2c"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "usuarios",
        sa.Column("origem_auth", sa.String(length=20), nullable=False, server_default="local"),
    )
    op.add_column(
        "usuarios",
        sa.Column("google_sub", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "usuarios",
        sa.Column("email_verificado", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index(op.f("ix_usuarios_google_sub"), "usuarios", ["google_sub"], unique=True)


def downgrade():
    op.drop_index(op.f("ix_usuarios_google_sub"), table_name="usuarios")
    op.drop_column("usuarios", "email_verificado")
    op.drop_column("usuarios", "google_sub")
    op.drop_column("usuarios", "origem_auth")
