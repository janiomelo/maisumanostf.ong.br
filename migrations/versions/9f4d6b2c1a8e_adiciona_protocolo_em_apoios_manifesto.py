"""adiciona protocolo em apoios_manifesto

Revision ID: 9f4d6b2c1a8e
Revises: 8c1d2e3f4a5b
Create Date: 2026-03-08 23:30:00.000000

"""

from datetime import datetime
import hashlib

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9f4d6b2c1a8e"
down_revision = "8c1d2e3f4a5b"
branch_labels = None
depends_on = None


def _gerar_protocolo_legado(email: str, criado_em: datetime, apoio_id: int) -> str:
    base = f"{criado_em.isoformat()}|{email}|{apoio_id}".encode("utf-8")
    return hashlib.sha256(base).hexdigest()


def upgrade():
    op.add_column("apoios_manifesto", sa.Column("protocolo", sa.String(length=64), nullable=True))

    conn = op.get_bind()
    registros = conn.execute(
        sa.text("SELECT id, email, criado_em FROM apoios_manifesto ORDER BY id ASC")
    ).fetchall()

    for apoio_id, email, criado_em in registros:
        protocolo = _gerar_protocolo_legado(email=email, criado_em=criado_em, apoio_id=apoio_id)
        conn.execute(
            sa.text("UPDATE apoios_manifesto SET protocolo = :protocolo WHERE id = :id"),
            {"protocolo": protocolo, "id": apoio_id},
        )

    with op.batch_alter_table("apoios_manifesto") as batch_op:
        batch_op.alter_column("protocolo", existing_type=sa.String(length=64), nullable=False)
        batch_op.create_index(op.f("ix_apoios_manifesto_protocolo"), ["protocolo"], unique=True)


def downgrade():
    with op.batch_alter_table("apoios_manifesto") as batch_op:
        batch_op.drop_index(op.f("ix_apoios_manifesto_protocolo"))
        batch_op.drop_column("protocolo")
