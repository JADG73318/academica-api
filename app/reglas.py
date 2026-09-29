"""Reglas de negocio puras (sin dependencias de FastAPI ni de la base de datos)."""
from datetime import date
from typing import Optional

NOTA_MINIMA_APROBAR = 3.0


def calcular_edad(nacimiento: date, hoy: Optional[date] = None) -> int:
    """Edad cumplida a la fecha indicada (por defecto, hoy)."""
    hoy = hoy or date.today()
    return hoy.year - nacimiento.year - ((hoy.month, hoy.day) < (nacimiento.month, nacimiento.day))


def calcular_nota_final(parcial1: float, parcial2: float, parcial3: float) -> float:
    """Promedio simple de los tres parciales, con dos decimales."""
    return round((parcial1 + parcial2 + parcial3) / 3, 2)


def determinar_estado(nota_final: float) -> str:
    """Aprobado si la nota final es 3.0 o más; de lo contrario, Reprobado."""
    return "Aprobado" if nota_final >= NOTA_MINIMA_APROBAR else "Reprobado"
