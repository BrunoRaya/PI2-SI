import tempfile
import unittest
from pathlib import Path

from app import create_app


class AttendanceFlowTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database = str(Path(self.temp_dir.name) / "test.db")
        self.app = create_app({"TESTING": True, "DATABASE": database, "SECRET_KEY": "test"})
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_complete_attendance_flow(self):
        response = self.client.post(
            "/recepcao/novo",
            data={
                "full_name": "Maria da Silva",
                "cpf": "12345678900",
                "rg": "1234567",
                "birth_date": "1990-05-10",
                "address": "Rua Central, 100",
                "phone": "19999999999",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"AT0001", response.data)

        response = self.client.post(
            "/triagem/1",
            data={
                "blood_pressure": "120/80",
                "temperature": "37,2",
                "heart_rate": "90",
                "complaints": "Dor de cabeca e nausea",
                "manchester": "amarelo",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"enviada ao painel medico", response.data)

        response = self.client.post(
            "/medico/1",
            data={"action": "medication", "name": "Dipirona", "dosage": "500 mg"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Dipirona", response.data)

        response = self.client.post(
            "/medico/1",
            data={"action": "finish", "medical_notes": "Paciente avaliada e liberada."},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"confirmado e finalizado", response.data)

        response = self.client.post("/recepcao/1/cancelar")
        self.assertEqual(response.status_code, 409)

    def test_doctor_panel_orders_by_manchester_priority(self):
        patients = (
            ("Paciente Verde", "11111111111", "verde"),
            ("Paciente Vermelho", "22222222222", "vermelho"),
        )
        for index, (name, cpf, priority) in enumerate(patients, start=1):
            self.client.post(
                "/recepcao/novo",
                data={
                    "full_name": name,
                    "cpf": cpf,
                    "birth_date": "1990-05-10",
                    "address": "Rua de Teste, 10",
                },
            )
            self.client.post(
                f"/triagem/{index}",
                data={
                    "blood_pressure": "120/80",
                    "temperature": "36,5",
                    "heart_rate": "80",
                    "complaints": "Queixa de teste",
                    "manchester": priority,
                },
            )

        response = self.client.get("/medico")
        html = response.data.decode("utf-8")
        self.assertLess(html.index("Paciente Vermelho"), html.index("Paciente Verde"))


if __name__ == "__main__":
    unittest.main()
