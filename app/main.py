"""Servicios web del Sistema Académica (GA7-220501096-AA5-EV01)."""
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Response
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles

from .database import get_db, iniciar_db
from .reglas import calcular_nota_final, determinar_estado
from .schemas import (AlumnoActualizar, AlumnoCrear, CatalogoCrear, NotaCrear,
                      ProgramaCrear, UsuarioLogin, UsuarioRegistro)
from .security import (crear_token, decodificar_token, hashear_password,
                       verificar_password)


@asynccontextmanager
async def lifespan(app: FastAPI):
    iniciar_db()
    yield


app = FastAPI(
    title="Sistema Académica - Servicios web",
    description="API REST para registro de alumnos, calificaciones e inicio de sesión.",
    version="1.0.0",
    lifespan=lifespan,
)

bearer = HTTPBearer(auto_error=False)
CARPETA_ESTATICA = Path(__file__).parent / "static"


# ---------------------------------------------------------------- utilidades
def usuario_actual(credenciales: HTTPAuthorizationCredentials = Depends(bearer),
                   db: sqlite3.Connection = Depends(get_db)) -> dict:
    """Exige un token válido en el encabezado Authorization: Bearer <token>."""
    error = HTTPException(status_code=401, detail="Token inválido o ausente",
                          headers={"WWW-Authenticate": "Bearer"})
    if credenciales is None:
        raise error
    datos = decodificar_token(credenciales.credentials)
    if datos is None:
        raise error
    fila = db.execute("SELECT id, nombre, email FROM usuarios WHERE id = ?",
                      (int(datos["sub"]),)).fetchone()
    if fila is None:
        raise error
    return dict(fila)


def existe(db: sqlite3.Connection, tabla: str, codigo) -> bool:
    # 'tabla' siempre es un valor fijo escrito en este archivo, nunca dato del usuario
    return db.execute(f"SELECT 1 FROM {tabla} WHERE codigo = ?", (codigo,)).fetchone() is not None


def alumno_o_404(db: sqlite3.Connection, codigo: int) -> dict:
    fila = db.execute("SELECT * FROM alumnos WHERE codigo = ?", (codigo,)).fetchone()
    if fila is None:
        raise HTTPException(status_code=404, detail="El alumno no existe")
    return dict(fila)


# ------------------------------------------------------- autenticación (login)
auth = APIRouter(prefix="/api/auth", tags=["Autenticación"])


@auth.post("/registro", status_code=201)
def registrar_usuario(datos: UsuarioRegistro, db: sqlite3.Connection = Depends(get_db)):
    """Servicio de registro de usuarios del sistema."""
    email = datos.email.lower()
    try:
        cur = db.execute(
            "INSERT INTO usuarios (nombre, email, password_hash) VALUES (?, ?, ?)",
            (datos.nombre, email, hashear_password(datos.password)))
        db.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="El correo ya está registrado")
    return {"id": cur.lastrowid, "nombre": datos.nombre, "email": email}


@auth.post("/login")
def iniciar_sesion(datos: UsuarioLogin, db: sqlite3.Connection = Depends(get_db)):
    """Servicio de inicio de sesión: devuelve un token JWT."""
    fila = db.execute("SELECT id, nombre, email, password_hash FROM usuarios WHERE email = ?",
                      (datos.email.lower(),)).fetchone()
    # Mismo mensaje para correo o contraseña incorrectos (no revela cuál falló)
    if fila is None or not verificar_password(datos.password, fila["password_hash"]):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    return {"access_token": crear_token(fila["id"], fila["email"]),
            "token_type": "bearer", "usuario": fila["nombre"]}


# ------------------------------------------ servicios protegidos (requieren token)
api = APIRouter(prefix="/api", dependencies=[Depends(usuario_actual)])


# ---- Alumnos (servicio de registro del prototipo "Registrar nuevo estudiante")
@api.post("/alumnos", status_code=201, tags=["Alumnos"])
def crear_alumno(a: AlumnoCrear, db: sqlite3.Connection = Depends(get_db)):
    if not existe(db, "programas", a.programa_codigo):
        raise HTTPException(status_code=404, detail="El programa no existe")
    try:
        db.execute(
            "INSERT INTO alumnos (codigo, nombre_completo, edad, fecha_nacimiento, ciudad, genero, programa_codigo) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (a.codigo, a.nombre_completo, a.edad, a.fecha_nacimiento.isoformat(),
             a.ciudad, a.genero, a.programa_codigo))
        db.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Ya existe un alumno con ese código")
    return alumno_o_404(db, a.codigo)


@api.get("/alumnos", tags=["Alumnos"])
def listar_alumnos(db: sqlite3.Connection = Depends(get_db)):
    return [dict(f) for f in db.execute("SELECT * FROM alumnos ORDER BY codigo").fetchall()]


@api.get("/alumnos/{codigo}", tags=["Alumnos"])
def consultar_alumno(codigo: int, db: sqlite3.Connection = Depends(get_db)):
    return alumno_o_404(db, codigo)


@api.put("/alumnos/{codigo}", tags=["Alumnos"])
def actualizar_alumno(codigo: int, a: AlumnoActualizar, db: sqlite3.Connection = Depends(get_db)):
    alumno_o_404(db, codigo)
    if not existe(db, "programas", a.programa_codigo):
        raise HTTPException(status_code=404, detail="El programa no existe")
    db.execute(
        "UPDATE alumnos SET nombre_completo=?, edad=?, fecha_nacimiento=?, ciudad=?, genero=?, programa_codigo=? "
        "WHERE codigo=?",
        (a.nombre_completo, a.edad, a.fecha_nacimiento.isoformat(), a.ciudad, a.genero,
         a.programa_codigo, codigo))
    db.commit()
    return alumno_o_404(db, codigo)


@api.delete("/alumnos/{codigo}", status_code=204, tags=["Alumnos"])
def eliminar_alumno(codigo: int, db: sqlite3.Connection = Depends(get_db)):
    alumno_o_404(db, codigo)
    db.execute("DELETE FROM alumnos WHERE codigo = ?", (codigo,))
    db.commit()
    return Response(status_code=204)


# ---- Catálogos (alimentan las listas desplegables)
@api.get("/programas", tags=["Catálogos"])
def listar_programas(db: sqlite3.Connection = Depends(get_db)):
    return [dict(f) for f in db.execute("SELECT * FROM programas ORDER BY codigo").fetchall()]


@api.post("/programas", status_code=201, tags=["Catálogos"])
def crear_programa(p: ProgramaCrear, db: sqlite3.Connection = Depends(get_db)):
    try:
        db.execute("INSERT INTO programas (codigo, nombre) VALUES (?, ?)", (p.codigo, p.nombre))
        db.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Ya existe un programa con ese código")
    return p


@api.get("/materias", tags=["Catálogos"])
def listar_materias(db: sqlite3.Connection = Depends(get_db)):
    return [dict(f) for f in db.execute("SELECT * FROM materias ORDER BY codigo").fetchall()]


@api.post("/materias", status_code=201, tags=["Catálogos"])
def crear_materia(m: CatalogoCrear, db: sqlite3.Connection = Depends(get_db)):
    try:
        db.execute("INSERT INTO materias (codigo, nombre) VALUES (?, ?)", (m.codigo, m.nombre))
        db.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Ya existe una materia con ese código")
    return m


@api.get("/profesores", tags=["Catálogos"])
def listar_profesores(db: sqlite3.Connection = Depends(get_db)):
    return [dict(f) for f in db.execute("SELECT * FROM profesores ORDER BY codigo").fetchall()]


@api.post("/profesores", status_code=201, tags=["Catálogos"])
def crear_profesor(p: CatalogoCrear, db: sqlite3.Connection = Depends(get_db)):
    try:
        db.execute("INSERT INTO profesores (codigo, nombre) VALUES (?, ?)", (p.codigo, p.nombre))
        db.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Ya existe un profesor con ese código")
    return p


# ---- Notas (prototipo "Registrar calificación": Guardar y calcular)
@api.post("/notas", status_code=201, tags=["Notas"])
def registrar_nota(n: NotaCrear, db: sqlite3.Connection = Depends(get_db)):
    if not existe(db, "alumnos", n.alumno_codigo):
        raise HTTPException(status_code=404, detail="El alumno no existe")
    if not existe(db, "materias", n.materia_codigo):
        raise HTTPException(status_code=404, detail="La materia no existe")
    if not existe(db, "profesores", n.profesor_codigo):
        raise HTTPException(status_code=404, detail="El profesor no existe")
    nota_final = calcular_nota_final(n.parcial1, n.parcial2, n.parcial3)
    estado = determinar_estado(nota_final)
    cur = db.execute(
        "INSERT INTO notas (alumno_codigo, materia_codigo, profesor_codigo, parcial1, parcial2, parcial3, "
        "nota_final, estado) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (n.alumno_codigo, n.materia_codigo, n.profesor_codigo, n.parcial1, n.parcial2, n.parcial3,
         nota_final, estado))
    db.commit()
    return {"id": cur.lastrowid, "alumno_codigo": n.alumno_codigo, "materia_codigo": n.materia_codigo,
            "profesor_codigo": n.profesor_codigo, "parcial1": n.parcial1, "parcial2": n.parcial2,
            "parcial3": n.parcial3, "nota_final": nota_final, "estado": estado}


@api.get("/notas", tags=["Notas"])
def notas_recientes(limite: int = Query(10, ge=1, le=100), db: sqlite3.Connection = Depends(get_db)):
    filas = db.execute(
        "SELECT n.id, n.alumno_codigo, a.nombre_completo AS alumno, m.nombre AS materia, "
        "p.nombre AS profesor, n.parcial1, n.parcial2, n.parcial3, n.nota_final, n.estado, n.fecha "
        "FROM notas n JOIN alumnos a ON a.codigo = n.alumno_codigo "
        "JOIN materias m ON m.codigo = n.materia_codigo "
        "JOIN profesores p ON p.codigo = n.profesor_codigo "
        "ORDER BY n.id DESC LIMIT ?", (limite,)).fetchall()
    return [dict(f) for f in filas]


# ---- Resumen académico (pantalla de inicio)
@api.get("/resumen", tags=["Resumen"])
def resumen(db: sqlite3.Connection = Depends(get_db)):
    def contar(sql: str) -> int:
        return db.execute(sql).fetchone()[0]
    return {"alumnos": contar("SELECT COUNT(*) FROM alumnos"),
            "materias": contar("SELECT COUNT(*) FROM materias"),
            "aprobadas": contar("SELECT COUNT(*) FROM notas WHERE estado = 'Aprobado'")}


app.include_router(auth)
app.include_router(api)


# ------------------------------------------------ interfaz web (prototipo Academica)
@app.get("/", include_in_schema=False)
def pagina_principal():
    return FileResponse(CARPETA_ESTATICA / "index.html")


app.mount("/static", StaticFiles(directory=CARPETA_ESTATICA), name="static")
