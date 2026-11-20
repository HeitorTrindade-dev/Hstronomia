import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.restaurante import Restaurante


class Despesa(Base):
    __tablename__ = "despesa"
    __table_args__ = (
        Index("ix_despesa_restaurante_data", "restaurante_id", "data_pagamento"),
        Index("ix_despesa_restaurante_categoria", "restaurante_id", "categoria"),
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
    descricao: Mapped[str] = mapped_column(String(200), nullable=False)
    categoria: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default="outros",
    )
    valor: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    data_pagamento: Mapped[date] = mapped_column(Date, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    restaurante: Mapped["Restaurante"] = relationship("Restaurante", back_populates="despesas")
