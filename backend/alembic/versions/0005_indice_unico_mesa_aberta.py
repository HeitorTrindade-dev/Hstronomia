"""adicionar indice unico parcial para mesa aberta em comanda

Revision ID: 0005_indice_unico_mesa_aberta
Revises: 0004_criar_tabela_despesa
Create Date: 2026-11-20

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005_indice_unico_mesa_aberta"
down_revision: str | None = "0004_criar_tabela_despesa"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "uq_comanda_restaurante_mesa_aberta",
        "comanda",
        ["restaurante_id", "numero_mesa"],
        unique=True,
        postgresql_where=sa.text("status = 'aberta' AND numero_mesa IS NOT NULL"),
        sqlite_where=sa.text("status = 'aberta' AND numero_mesa IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_comanda_restaurante_mesa_aberta", table_name="comanda")
