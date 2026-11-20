import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.item_comanda import ItemComanda
    from src.models.restaurante import Restaurante


class Comanda(Base):
    __tablename__ = "comanda"
    __table_args__ = (
        Index("ix_comanda_restaurante_status", "restaurante_id", "status"),
        Index("ix_comanda_restaurante_mesa_status", "restaurante_id", "numero_mesa", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    restaurante_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("restaurante.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Atendimento
    numero_mesa: Mapped[int | None] = mapped_column(Integer, nullable=True)
    identificador: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tipo_atendimento: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="mesa",
        server_default=text("'mesa'"),
    )

    # Financeiro
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="aberta",
        server_default=text("'aberta'"),
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default=text("0"),
    )
    taxa_servico: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default=text("0"),
    )
    desconto: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default=text("0"),
    )
    valor_total: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default=text("0"),
    )
    metodo_pagamento: Mapped[str | None] = mapped_column(String(50), nullable=True)

    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    fechado_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    restaurante: Mapped["Restaurante"] = relationship("Restaurante", back_populates="comandas")
    itens: Mapped[list["ItemComanda"]] = relationship(
        "ItemComanda",
        back_populates="comanda",
        cascade="all, delete-orphan",
    )
