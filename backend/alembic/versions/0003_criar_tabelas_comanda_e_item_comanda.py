"""criar tabelas comanda e item_comanda

Revision ID: 0003_comanda_item_comanda
Revises: 0002_criar_tabela_item
Create Date: 2026-11-20

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_comanda_item_comanda"
down_revision: str | None = "0002_criar_tabela_item"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "comanda",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "restaurante_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("restaurante.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("numero_mesa", sa.Integer(), nullable=True),
        sa.Column("identificador", sa.String(length=100), nullable=True),
        sa.Column(
            "tipo_atendimento",
            sa.String(length=20),
            server_default=sa.text("'mesa'"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'aberta'"),
            nullable=False,
        ),
        sa.Column(
            "subtotal",
            sa.Numeric(precision=10, scale=2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "taxa_servico",
            sa.Numeric(precision=10, scale=2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "desconto",
            sa.Numeric(precision=10, scale=2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "valor_total",
            sa.Numeric(precision=10, scale=2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("metodo_pagamento", sa.String(length=50), nullable=True),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("fechado_em", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f("ix_comanda_restaurante_id"), "comanda", ["restaurante_id"], unique=False)
    op.create_index(
        "ix_comanda_restaurante_status",
        "comanda",
        ["restaurante_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_comanda_restaurante_mesa_status",
        "comanda",
        ["restaurante_id", "numero_mesa", "status"],
        unique=False,
    )

    op.create_table(
        "item_comanda",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "comanda_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("comanda.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("item.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("nome_item", sa.String(length=120), nullable=False),
        sa.Column(
            "quantidade",
            sa.Integer(),
            server_default=sa.text("1"),
            nullable=False,
        ),
        sa.Column("preco_unitario", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'pendente'"),
            nullable=False,
        ),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        op.f("ix_item_comanda_comanda_id"),
        "item_comanda",
        ["comanda_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_item_comanda_item_id"),
        "item_comanda",
        ["item_id"],
        unique=False,
    )
    op.create_index(
        "ix_item_comanda_comanda_status",
        "item_comanda",
        ["comanda_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_item_comanda_comanda_status", table_name="item_comanda")
    op.drop_index(op.f("ix_item_comanda_item_id"), table_name="item_comanda")
    op.drop_index(op.f("ix_item_comanda_comanda_id"), table_name="item_comanda")
    op.drop_table("item_comanda")

    op.drop_index("ix_comanda_restaurante_mesa_status", table_name="comanda")
    op.drop_index("ix_comanda_restaurante_status", table_name="comanda")
    op.drop_index(op.f("ix_comanda_restaurante_id"), table_name="comanda")
    op.drop_table("comanda")
