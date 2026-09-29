# Sistema Académica - Servicios web (GA7-220501096-AA5-EV01)

API REST con **Python + FastAPI + SQLite** para el caso "Academica": registro de alumnos,
registro de calificaciones e inicio de sesión.

## 1. Ejecutar el proyecto

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate      Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Abre **http://127.0.0.1:8000/** para usar la interfaz web (igual a los prototipos: inicio con resumen académico,
registro de estudiantes y registro de calificaciones). Crea tu cuenta con «Crear cuenta» y luego inicia sesión.
La documentación técnica de los servicios (Swagger) está en http://127.0.0.1:8000/docs.
La base de datos `academica.db` se crea sola al iniciar, con un programa, tres materias y un profesor de ejemplo.

## 2. Probar en Swagger (opcional, orden sugerido)

1. `POST /api/auth/registro` : crea un usuario (contraseña de 8+ caracteres con letras y números).
2. `POST /api/auth/login` : copia el `access_token`.
3. Botón **Authorize** (candado): pega el token.
4. `POST /api/alumnos` : registra un alumno (la edad debe coincidir con la fecha de nacimiento).
5. `POST /api/notas` : con parciales 4.3, 4.2 y 3.8 devuelve nota final 4.1 y estado Aprobado.
6. `GET /api/resumen` y `GET /api/notas` : datos de la pantalla de inicio.

## 3. Servicios

| Método | Ruta | Descripción |
|---|---|---|
| POST | /api/auth/registro | Registro de usuarios |
| POST | /api/auth/login | Inicio de sesión (devuelve JWT) |
| POST/GET | /api/alumnos | Registrar / listar alumnos |
| GET/PUT/DELETE | /api/alumnos/{codigo} | Consultar / actualizar / eliminar |
| GET/POST | /api/programas, /api/materias, /api/profesores | Catálogos |
| POST | /api/notas | Registrar calificación y calcular nota final |
| GET | /api/notas | Notas recientes |
| GET | /api/resumen | Totales de alumnos, materias y aprobadas |

Todos, salvo registro y login, requieren `Authorization: Bearer <token>`.

## 4. Validaciones

- Campos obligatorios y longitudes mínimas/máximas; correo con formato válido.
- Contraseña de 8 a 64 caracteres con letras y números; se guarda cifrada (PBKDF2), nunca en claro.
- Notas entre 0.0 y 5.0. Nota final = promedio de los tres parciales. Aprobado si es 3.0 o más.
- Edad coherente con la fecha de nacimiento; la fecha no puede ser futura.
- Código de alumno único (409) y referencias existentes: programa, alumno, materia, profesor (404).
- Datos inválidos devuelven 422; sin token o token inválido, 401.

## 5. Pruebas

```bash
python -m unittest discover -s tests -v
```

## 6. Versionamiento con Git y GitHub

```bash
git init
git add .
git commit -m "feat: estructura inicial del proyecto FastAPI"
git remote add origin https://github.com/USUARIO/academica-api.git
git branch -M main
git push -u origin main
```

Se recomienda un commit por etapa, por ejemplo:
`feat: base de datos`, `feat: servicio de registro de alumnos`, `feat: login con JWT`,
`feat: registro de notas`, `test: pruebas`, `docs: README`.
