"""Base de datos SQLite: creación de tablas, datos iniciales y conexión por petición."""
import os
import sqlite3

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.getenv("DB_PATH", os.path.join(RAIZ, "academica.db"))

ESQUEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre        TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS programas (
    codigo TEXT PRIMARY KEY,
    nombre TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS materias (
    codigo INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS profesores (
    codigo INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS alumnos (
    codigo           INTEGER PRIMARY KEY,
    nombre_completo  TEXT NOT NULL,
    edad             INTEGER NOT NULL,
    fecha_nacimiento TEXT NOT NULL,
    ciudad           TEXT NOT NULL,
    genero           TEXT NOT NULL,
    programa_codigo  TEXT NOT NULL REFERENCES programas(codigo)
);
CREATE TABLE IF NOT EXISTS notas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    alumno_codigo   INTEGER NOT NULL REFERENCES alumnos(codigo) ON DELETE CASCADE,
    materia_codigo  INTEGER NOT NULL REFERENCES materias(codigo),
    profesor_codigo INTEGER NOT NULL REFERENCES profesores(codigo),
    parcial1        REAL NOT NULL,
    parcial2        REAL NOT NULL,
    parcial3        REAL NOT NULL,
    nota_final      REAL NOT NULL,
    estado          TEXT NOT NULL,
    fecha           TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

# Datos de ejemplo tomados del prototipo (listas desplegables del formulario)
DATOS_INICIALES = [
    ("INSERT OR IGNORE INTO programas (codigo, nombre) VALUES (?, ?)", [("01", "Ingeniería de Sistemas")]),
    ("INSERT OR IGNORE INTO materias (codigo, nombre) VALUES (?, ?)",
     [(10, "Bases de Datos"), (11, "Programación Web"), (12, "Telemática")]),
    ("INSERT OR IGNORE INTO profesores (codigo, nombre) VALUES (?, ?)", [(10, "Denis Colunge")]),
]


def conectar() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def iniciar_db() -> None:
    conn = conectar()
    try:
        conn.executescript(ESQUEMA)
        for sql, filas in DATOS_INICIALES:
            conn.executemany(sql, filas)
        conn.commit()
    finally:
        conn.close()


def get_db():
    """Dependencia de FastAPI: una conexión por petición, cerrada al terminar."""
    conn = conectar()
    try:
        yield conn
    finally:
        conn.close()
