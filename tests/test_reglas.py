import os
import tempfile
import unittest
from datetime import date

os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "reglas.db")

from app import database, security
from app.reglas import calcular_edad, calcular_nota_final, determinar_estado


class TestReglas(unittest.TestCase):
    def test_nota_final_del_prototipo(self):
        self.assertEqual(calcular_nota_final(4.3, 4.2, 3.8), 4.1)

    def test_estado(self):
        self.assertEqual(determinar_estado(4.1), "Aprobado")
        self.assertEqual(determinar_estado(3.0), "Aprobado")
        self.assertEqual(determinar_estado(2.6), "Reprobado")

    def test_edad(self):
        self.assertEqual(calcular_edad(date(2006, 4, 15), date(2026, 9, 23)), 20)
        self.assertEqual(calcular_edad(date(2006, 4, 15), date(2026, 4, 14)), 19)


class TestSeguridad(unittest.TestCase):
    def test_password_hash(self):
        h = security.hashear_password("Clave1234")
        self.assertNotIn("Clave1234", h)
        self.assertTrue(security.verificar_password("Clave1234", h))
        self.assertFalse(security.verificar_password("otra", h))

    def test_token(self):
        t = security.crear_token(7, "a@b.co")
        self.assertEqual(security.decodificar_token(t)["sub"], "7")
        self.assertIsNone(security.decodificar_token(t + "x"))


class TestBaseDatos(unittest.TestCase):
    def test_datos_iniciales(self):
        database.iniciar_db()
        database.iniciar_db()  # debe poder ejecutarse dos veces sin duplicar
        conn = database.conectar()
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM materias").fetchone()[0], 3)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM programas").fetchone()[0], 1)
        conn.close()


if __name__ == "__main__":
    unittest.main()
