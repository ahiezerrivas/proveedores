import json
import tempfile

from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from rest_framework.test import APIClient

from .models import Proveedor


class ProveedorModelTests(TestCase):
    def test_str_includes_supplier_and_contract(self):
        proveedor = Proveedor.objects.create(
            proveedor="Servicios del Norte",
            contrato="CT-2026-01",
            tarifa_mensual="250.00",
            servicios="Soporte técnico",
        )
        self.assertEqual(str(proveedor), "Servicios del Norte — CT-2026-01")


class ProveedorPermissionTests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)
        media_settings = override_settings(MEDIA_ROOT=self.media_dir.name)
        media_settings.enable()
        self.addCleanup(media_settings.disable)
        self.client = APIClient()
        self.url = "/api/proveedores/"
        self.consulta = User.objects.create_user(username="consulta", password="test-password")
        self.consulta.groups.add(Group.objects.get(name="Consulta"))
        self.administrador = User.objects.create_user(username="admin", password="test-password")
        self.administrador.groups.add(Group.objects.get(name="Administradores"))

    def test_anonymous_user_cannot_read_proveedores(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_consulta_role_can_read_but_cannot_create(self):
        self.client.force_authenticate(self.consulta)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        proveedor = Proveedor.objects.create(
            proveedor="Servicios del Norte",
            contrato="CT-2026-01",
            tarifa_mensual="250.00",
            servicios="Soporte técnico",
        )
        response = self.client.post(
            self.url,
            {
                "proveedor": "Servicios del Norte",
                "contrato": "CT-2026-01",
                "tarifa_mensual": "250.00",
                "servicios": "Soporte técnico",
                "estado": "Activo",
            },
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            self.client.patch(
                f"{self.url}{proveedor.pk}/",
                {"estado": "Inactivo"},
                format="json",
            ).status_code,
            403,
        )
        self.assertEqual(self.client.delete(f"{self.url}{proveedor.pk}/").status_code, 403)

    def test_administradores_role_can_create_edit_and_delete(self):
        self.client.force_authenticate(self.administrador)
        response = self.client.post(
            self.url,
            {
                "proveedor": "Servicios del Norte",
                "contrato": "CT-2026-01",
                "tarifa_mensual": "250.00",
                "servicios": "Soporte técnico",
                "estado": "Activo",
            },
        )
        self.assertEqual(response.status_code, 201)
        proveedor_url = f"{self.url}{response.data['id']}/"
        self.assertEqual(
            self.client.patch(proveedor_url, {"estado": "Inactivo"}, format="json").status_code,
            200,
        )
        self.assertEqual(self.client.delete(proveedor_url).status_code, 204)

    def test_admin_can_attach_and_download_a_pdf(self):
        self.client.force_authenticate(self.administrador)
        response = self.client.post(
            self.url,
            {
                "proveedor": "Servicios del Norte",
                "contrato": "CT-2026-01",
                "tarifa_mensual": "250.00",
                "servicios": "Soporte técnico",
                "estado": "Activo",
                "archivo_pdf": SimpleUploadedFile(
                    "contrato.pdf",
                    b"%PDF-1.4\ncontrato de prueba",
                    content_type="application/pdf",
                ),
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["tiene_pdf"])
        download = self.client.get(f"{self.url}{response.data['id']}/pdf/")
        self.assertEqual(download.status_code, 200)
        self.assertEqual(download["Content-Type"], "application/pdf")
        self.assertTrue(download["Content-Disposition"].startswith("inline;"))
        self.assertIn(b"%PDF-1.4", b"".join(download.streaming_content))

    def test_rejects_file_that_is_not_a_pdf(self):
        self.client.force_authenticate(self.administrador)
        response = self.client.post(
            self.url,
            {
                "proveedor": "Servicios del Norte",
                "contrato": "CT-2026-01",
                "tarifa_mensual": "250.00",
                "servicios": "Soporte técnico",
                "estado": "Activo",
                "archivo_pdf": SimpleUploadedFile(
                    "contrato.pdf",
                    b"esto no es un PDF",
                    content_type="application/pdf",
                ),
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Proveedor.objects.exists())

    def test_pdf_download_requires_an_authenticated_user(self):
        self.client.force_authenticate(self.administrador)
        response = self.client.post(
            self.url,
            {
                "proveedor": "Servicios del Norte",
                "contrato": "CT-2026-01",
                "tarifa_mensual": "250.00",
                "servicios": "Soporte técnico",
                "estado": "Activo",
                "archivo_pdf": SimpleUploadedFile(
                    "contrato.pdf",
                    b"%PDF-1.4\ncontrato de prueba",
                    content_type="application/pdf",
                ),
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 201)
        pdf_url = f"{self.url}{response.data['id']}/pdf/"
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(pdf_url).status_code, 403)


class AuthenticationTests(TestCase):
    def test_login_requires_csrf_and_creates_a_session(self):
        user = User.objects.create_user(username="admin", password="test-password")
        user.groups.add(Group.objects.get(name="Administradores"))
        client = Client(enforce_csrf_checks=True)
        csrf_response = client.get("/api/auth/csrf/")
        csrf_token = csrf_response.json()["csrf_token"]

        response = client.post(
            "/api/auth/login/",
            data=json.dumps({"username": "admin", "password": "test-password"}),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["user"]["is_admin"])
        self.assertEqual(client.get("/api/auth/session/").json()["authenticated"], True)
