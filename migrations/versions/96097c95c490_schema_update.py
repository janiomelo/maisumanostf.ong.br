"""schema update

Revision ID: 96097c95c490
Revises: 
Create Date: 2026-03-07 18:50:52.033417

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '96097c95c490'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'wiki_paginas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('slug', sa.String(length=120), nullable=False),
        sa.Column('titulo', sa.String(length=255), nullable=False),
        sa.Column('conteudo_markdown', sa.Text(), nullable=False),
        sa.Column('criado_em', sa.DateTime(), nullable=False),
        sa.Column('atualizado_em', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_wiki_paginas_slug'), 'wiki_paginas', ['slug'], unique=True)


def downgrade():
    op.drop_index(op.f('ix_wiki_paginas_slug'), table_name='wiki_paginas')
    op.drop_table('wiki_paginas')
