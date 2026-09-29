"""Cifrado de contraseñas y manejo de tokens JWT."""
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

SECRET_KEY = os.getenv("SECRET_KEY", "clave-de-desarrollo-cambiar-en-produccion-2026")
ALGORITMO = "HS256"
MINUTOS_EXPIRACION = 60
ITERACIONES = 200_000


def hashear_password(password: str) -> str:
    """Devuelve 'sal$hash' usando PBKDF2-HMAC-SHA256 (nunca se guarda la contraseña en claro)."""
    sal = os.urandom(16)
    derivada = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), sal, ITERACIONES)
    return f"{sal.hex()}${derivada.hex()}"


def verificar_password(password: str, guardado: str) -> bool:
    try:
        sal_hex, hash_hex = guardado.split("$")
        sal = bytes.fromhex(sal_hex)
    except ValueError:
        return False
    derivada = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), sal, ITERACIONES)
    return hmac.compare_digest(derivada.hex(), hash_hex)


def crear_token(usuario_id: int, email: str) -> str:
    ahora = datetime.now(timezone.utc)
    payload = {
        "sub": str(usuario_id),
        "email": email,
        "iat": ahora,
        "exp": ahora + timedelta(minutes=MINUTOS_EXPIRACION),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITMO)


def decodificar_token(token: str) -> Optional[dict]:
    """Devuelve el contenido del token o None si es inválido o expiró."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITMO])
    except jwt.PyJWTError:
        return None
