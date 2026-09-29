"""Pruebas de los servicios web. Requieren: pip install -r requirements.txt"""
import os
import tempfile
import unittest
from datetime import date

os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "api.db")

from fastapi.testclient import TestClient

from app.main import app
from app.reglas import calcular_edad

NACIMIENTO = date(2006, 4, 15)


class TestAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cm = TestClient(app)
        cls.client = cls.cm.__enter__()  # ejecuta el inicio de la app (crea tablas)
        cls.client.post("/api/auth/registro", json={
            "nombre": "Admin Sistema", "email": "admin@academica.co", "password": "Clave1234"})
        r = cls.client.post("/api/auth/login", json={"email": "admin@academica.co", "password": "Clave1234"})
        cls.h = {"Authorization": "Bearer " + r.json()["access_token"]}

    @classmethod
    def tearDownClass(cls):
        cls.cm.__exit__(None, None, None)

    def alumno(self, codigo=4000, **extra):
        datos = {"codigo": codigo, "nombre_completo": "Laura Martínez", "edad": calcular_edad(NACIMIENTO),
                 "fecha_nacimiento": NACIMIENTO.isoformat(), "ciudad": "Pasto",
                 "genero": "Femenino", "programa_codigo": "01"}
        datos.update(extra)
        return datos

    def test_1_registro_duplicado_y_validaciones(self):
        r = self.client.post("/api/auth/registro", json={
            "nombre": "Admin Sistema", "email": "admin@academica.co", "password": "Clave1234"})
        self.assertEqual(r.status_code, 409)
        r = self.client.post("/api/auth/registro", json={
            "nombre": "Otro Usuario", "email": "no-es-correo", "password": "Clave1234"})
        self.assertEqual(r.status_code, 422)
        r = self.client.post("/api/auth/registro", json={
            "nombre": "Otro Usuario", "email": "otro@academica.co", "password": "sololetras"})
        self.assertEqual(r.status_code, 422)

    def test_2_login_incorrecto(self):
        r = self.client.post("/api/auth/login", json={"email": "admin@academica.co", "password": "Mala1234"})
        self.assertEqual(r.status_code, 401)

    def test_3_sin_token(self):
        self.assertEqual(self.client.get("/api/alumnos").status_code, 401)

    def test_4_alumnos(self):
        r = self.client.post("/api/alumnos", json=self.alumno(), headers=self.h)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(self.client.post("/api/alumnos", json=self.alumno(), headers=self.h).status_code, 409)
        r = self.client.post("/api/alumnos", json=self.alumno(4001, programa_codigo="99"), headers=self.h)
        self.assertEqual(r.status_code, 404)
        r = self.client.post("/api/alumnos", json=self.alumno(4002, edad=50), headers=self.h)
        self.assertEqual(r.status_code, 422)  # edad no coincide con la fecha de nacimiento
        self.assertEqual(self.client.get("/api/alumnos/4000", headers=self.h).status_code, 200)

    def test_5_nota_del_prototipo(self):
        self.client.post("/api/alumnos", json=self.alumno(4010), headers=self.h)
        cuerpo = {"alumno_codigo": 4010, "materia_codigo": 10, "profesor_codigo": 10,
                  "parcial1": 4.3, "parcial2": 4.2, "parcial3": 3.8}
        r = self.client.post("/api/notas", json=cuerpo, headers=self.h)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["nota_final"], 4.1)
        self.assertEqual(r.json()["estado"], "Aprobado")
        cuerpo["parcial1"] = 5.5
        self.assertEqual(self.client.post("/api/notas", json=cuerpo, headers=self.h).status_code, 422)
        r = self.client.get("/api/resumen", headers=self.h)
        self.assertGreaterEqual(r.json()["aprobadas"], 1)


if __name__ == "__main__":
    unittest.main()
