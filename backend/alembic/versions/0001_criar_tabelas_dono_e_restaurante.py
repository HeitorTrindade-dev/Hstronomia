"""criar tabelas dono e restaurante

Revision ID: 0001_dono_restaurante
Revises:
Create Date: 2026-11-20

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_dono_restaurante"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "dono",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("senha_hash", sa.String(length=255), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_dono_email"), "dono", ["email"], unique=True)

    op.create_table(
        "restaurante",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("dono_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("dono.id", ondelete="CASCADE"), nullable=False),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("codigo_garcom", sa.String(length=20), nullable=False),
        sa.Column("codigo_cozinha", sa.String(length=20), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_restaurante_dono_id"), "restaurante", ["dono_id"], unique=False)
    op.create_index(op.f("ix_restaurante_slug"), "restaurante", ["slug"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_restaurante_slug"), table_name="restaurante")
    op.drop_index(op.f("ix_restaurante_dono_id"), table_name="restaurante")
    op.drop_table("restaurante")
    op.drop_index(op.f("ix_dono_email"), table_name="dono")
    op.drop_table("dono")
