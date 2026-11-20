"""criar tabela despesa

Revision ID: 0004_criar_tabela_despesa
Revises: 0003_comanda_item_comanda
Create Date: 2026-11-20

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004_criar_tabela_despesa"
down_revision: str | None = "0003_comanda_item_comanda"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "despesa",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "restaurante_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("restaurante.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("descricao", sa.String(length=200), nullable=False),
        sa.Column("categoria", sa.String(length=50), nullable=True),
        sa.Column("valor", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("data_pagamento", sa.Date(), nullable=False),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(op.f("ix_despesa_restaurante_id"), "despesa", ["restaurante_id"], unique=False)
    op.create_index(
        "ix_despesa_restaurante_data",
        "despesa",
        ["restaurante_id", "data_pagamento"],
        unique=False,
    )
    op.create_index(
        "ix_despesa_restaurante_categoria",
        "despesa",
        ["restaurante_id", "categoria"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_despesa_restaurante_categoria", table_name="despesa")
    op.drop_index("ix_despesa_restaurante_data", table_name="despesa")
    op.drop_index(op.f("ix_despesa_restaurante_id"), table_name="despesa")
    op.drop_table("despesa")
