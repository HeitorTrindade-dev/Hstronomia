"""criar tabela item

Revision ID: 0002_criar_tabela_item
Revises: 0001_dono_restaurante
Create Date: 2026-11-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002_criar_tabela_item"
down_revision: Union[str, None] = "0001_dono_restaurante"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "item",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "restaurante_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("restaurante.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("preco", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("disponivel", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("ativo", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_item_restaurante_id"), "item", ["restaurante_id"], unique=False)
    op.create_index("ix_item_restaurante_ativo", "item", ["restaurante_id", "ativo"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_item_restaurante_ativo", table_name="item")
    op.drop_index(op.f("ix_item_restaurante_id"), table_name="item")
    op.drop_table("item")
