"""Modelos de entrada con las validaciones de verificación (Pydantic)."""
from datetime import date
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from .reglas import calcular_edad


class UsuarioRegistro(BaseModel):
    nombre: str = Field(min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=64)

    @field_validator("nombre")
    @classmethod
    def nombre_sin_espacios_extra(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("El nombre debe tener al menos 3 caracteres")
        return v

    @field_validator("password")
    @classmethod
    def password_segura(cls, v: str) -> str:
        if not any(c.isalpha() for c in v) or not any(c.isdigit() for c in v):
            raise ValueError("La contraseña debe contener letras y números")
        return v


class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class AlumnoActualizar(BaseModel):
    nombre_completo: str = Field(min_length=3, max_length=100)
    edad: int = Field(ge=5, le=100)
    fecha_nacimiento: date
    ciudad: str = Field(min_length=2, max_length=60)
    genero: Literal["Femenino", "Masculino", "Otro"]
    programa_codigo: str = Field(min_length=1, max_length=10)

    @model_validator(mode="after")
    def edad_coherente(self):
        if self.fecha_nacimiento > date.today():
            raise ValueError("La fecha de nacimiento no puede ser futura")
        if calcular_edad(self.fecha_nacimiento) != self.edad:
            raise ValueError("La edad no coincide con la fecha de nacimiento")
        return self


class AlumnoCrear(AlumnoActualizar):
    codigo: int = Field(gt=0)


class NotaCrear(BaseModel):
    alumno_codigo: int = Field(gt=0)
    materia_codigo: int = Field(gt=0)
    profesor_codigo: int = Field(gt=0)
    parcial1: float = Field(ge=0.0, le=5.0)
    parcial2: float = Field(ge=0.0, le=5.0)
    parcial3: float = Field(ge=0.0, le=5.0)


class ProgramaCrear(BaseModel):
    codigo: str = Field(min_length=1, max_length=10)
    nombre: str = Field(min_length=3, max_length=100)


class CatalogoCrear(BaseModel):
    """Para materias y profesores (código numérico + nombre)."""
    codigo: int = Field(gt=0)
    nombre: str = Field(min_length=3, max_length=100)
