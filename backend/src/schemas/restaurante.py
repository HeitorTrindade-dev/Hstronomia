import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _validar_pin(value: str) -> str:
    pin_limpo = value.strip()
    if not pin_limpo.isdigit() or not (4 <= len(pin_limpo) <= 20):
        raise ValueError("O PIN deve conter entre 4 e 20 dígitos numéricos.")
    return pin_limpo


class RestauranteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: str = Field(..., min_length=2, max_length=120)
    slug: str = Field(..., min_length=2, max_length=100)
    codigo_garcom: str = Field(..., min_length=4, max_length=20)
    codigo_cozinha: str = Field(..., min_length=4, max_length=20)

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("O nome não pode conter caracteres nulos.")
        limpo = value.strip()
        if len(limpo) < 2:
            raise ValueError("O nome do restaurante deve ter pelo menos 2 caracteres.")
        return limpo

    @field_validator("slug")
    @classmethod
    def validar_slug(cls, value: str) -> str:
        normalizado = value.strip().lower()
        if len(normalizado) < 2 or not SLUG_PATTERN.match(normalizado):
            raise ValueError(
                "O slug deve conter apenas letras minúsculas, números e hífens (ex: 'meu-restaurante')."
            )
        return normalizado

    @field_validator("codigo_garcom", "codigo_cozinha")
    @classmethod
    def validar_pins_numericos(cls, value: str) -> str:
        return _validar_pin(value)

    @model_validator(mode="after")
    def validar_pins_distintos(self) -> "RestauranteCreate":
        if self.codigo_garcom == self.codigo_cozinha:
            raise ValueError(
                "O PIN do garçom e o PIN da cozinha devem ser diferentes."
            )
        return self


class RestauranteUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: str | None = Field(default=None, min_length=2, max_length=120)
    slug: str | None = Field(default=None, min_length=2, max_length=100)

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if "\x00" in value:
            raise ValueError("O nome não pode conter caracteres nulos.")
        limpo = value.strip()
        if len(limpo) < 2:
            raise ValueError("O nome do restaurante deve ter pelo menos 2 caracteres.")
        return limpo

    @field_validator("slug")
    @classmethod
    def validar_slug(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalizado = value.strip().lower()
        if len(normalizado) < 2 or not SLUG_PATTERN.match(normalizado):
            raise ValueError(
                "O slug deve conter apenas letras minúsculas, números e hífens (ex: 'meu-restaurante')."
            )
        return normalizado

    @model_validator(mode="after")
    def validar_campos_atualizacao(self) -> "RestauranteUpdate":
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualização.")
        for field_name in self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"O campo '{field_name}' não pode ser nulo.")
        return self


class RestaurantePinsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    codigo_garcom: str | None = Field(default=None, min_length=4, max_length=20)
    codigo_cozinha: str | None = Field(default=None, min_length=4, max_length=20)

    @field_validator("codigo_garcom", "codigo_cozinha")
    @classmethod
    def validar_pin_opcional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _validar_pin(value)

    @model_validator(mode="after")
    def validar_pelo_menos_um_pin(self) -> "RestaurantePinsUpdate":
        if self.codigo_garcom is None and self.codigo_cozinha is None:
            raise ValueError("Informe ao menos um PIN para atualização.")
        if (
            self.codigo_garcom is not None
            and self.codigo_cozinha is not None
            and self.codigo_garcom == self.codigo_cozinha
        ):
            raise ValueError(
                "O PIN do garçom e o PIN da cozinha devem ser diferentes."
            )
        return self


class RestauranteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    dono_id: uuid.UUID
    nome: str
    slug: str
    codigo_garcom: str
    codigo_cozinha: str
    criado_em: datetime


class RestaurantePublicoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str
    slug: str
