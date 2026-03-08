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


def _normalizar_criado_em(criado_em: datetime | str | None) -> str:
    if isinstance(criado_em, datetime):
        return criado_em.isoformat()

    if isinstance(criado_em, str):
        return criado_em.strip()

    return ""


def _gerar_protocolo_legado(email: str, criado_em: datetime | str | None, apoio_id: int) -> str:
    criado_em_str = _normalizar_criado_em(criado_em)
    base = f"{criado_em_str}|{email}|{apoio_id}".encode("utf-8")
    return hashlib.sha256(base).hexdigest()


def upgrade():
    conn = op.get_bind()
    insp = sa.inspect(conn)

    colunas = {c["name"] for c in insp.get_columns("apoios_manifesto")}
    if "protocolo" not in colunas:
        op.add_column("apoios_manifesto", sa.Column("protocolo", sa.String(length=64), nullable=True))

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

    indices = {idx["name"] for idx in sa.inspect(conn).get_indexes("apoios_manifesto")}
    indice = op.f("ix_apoios_manifesto_protocolo")
    if indice not in indices:
        op.create_index(indice, "apoios_manifesto", ["protocolo"], unique=True)


def downgrade():
    with op.batch_alter_table("apoios_manifesto") as batch_op:
        batch_op.drop_index(op.f("ix_apoios_manifesto_protocolo"))
        batch_op.drop_column("protocolo")
