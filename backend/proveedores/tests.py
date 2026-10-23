import json
import tempfile

from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import Client, TestCase, TransactionTestCase, override_settings
from rest_framework.test import APIClient

from .models import Contrato, Proveedor, RegistroAuditoria


class ProveedorModelTests(TestCase):
    def test_str_includes_supplier_and_contract(self):
        proveedor = Proveedor.objects.create(
            codigo="PR-001",
            nombre="Servicios del Norte",
        )
        contrato = Contrato.objects.create(
            proveedor=proveedor,
            contrato="CT-2026-01",
            tarifa_mensual="250.00",
            tarifa_trimestral="700.00",
            tarifa_semestral="1300.00",
            tarifa_anual="2400.00",
            servicios="Soporte técnico",
        )
        self.assertEqual(str(contrato), "Servicios del Norte — CT-2026-01")


class NormalizationMigrationTests(TransactionTestCase):
    def test_existing_rows_are_migrated_to_suppliers_and_contracts(self):
        targets = MigrationExecutor(connection).loader.graph.leaf_nodes()
        old_target = [("proveedores", "0005_proveedor_campos_opcionales")]

        try:
            MigrationExecutor(connection).migrate(old_target)
            old_apps = MigrationExecutor(connection).loader.project_state(old_target).apps
            ProveedorAnterior = old_apps.get_model("proveedores", "Proveedor")
            registros = [
                ProveedorAnterior.objects.create(
                    proveedor="Servicios del Norte",
                    contrato="CT-2026-01",
                    tarifa_mensual="250.00",
                    tarifa_trimestral="700.00",
                    tarifa_semestral="1300.00",
                    tarifa_anual="2400.00",
                    servicios="Soporte técnico",
                    documento_pdf="proveedores/contratos/contrato.pdf",
                ),
                ProveedorAnterior.objects.create(
                    proveedor="Servicios del Norte",
                    contrato="CT-2026-02",
                    tarifa_mensual="300.00",
                    tarifa_trimestral="800.00",
                    tarifa_semestral="1500.00",
                    tarifa_anual="2800.00",
                    servicios="Mantenimiento",
                    estado="Pendiente",
                ),
                ProveedorAnterior.objects.create(
                    proveedor="Servicios del Norte ",
                    contrato="CT-2026-03",
                    tarifa_mensual="100.00",
                    tarifa_trimestral="250.00",
                    tarifa_semestral="500.00",
                    tarifa_anual="900.00",
                    servicios="Instalación",
                ),
            ]

            MigrationExecutor(connection).migrate(targets)
            new_apps = MigrationExecutor(connection).loader.project_state(targets).apps
            ProveedorNuevo = new_apps.get_model("proveedores", "Proveedor")
            ContratoNuevo = new_apps.get_model("proveedores", "Contrato")
            contratos = list(ContratoNuevo.objects.order_by("id"))

            self.assertEqual(ProveedorNuevo.objects.count(), 2)
            self.assertEqual(ContratoNuevo.objects.count(), 3)
            self.assertEqual(
                [contrato.pk for contrato in contratos],
                [registro.pk for registro in registros],
            )
            self.assertEqual(contratos[0].proveedor_id, contratos[1].proveedor_id)
            self.assertNotEqual(contratos[1].proveedor_id, contratos[2].proveedor_id)
            self.assertEqual(str(contratos[0].tarifa_anual), "2400.00")
            self.assertEqual(contratos[0].documento_pdf.name, "proveedores/contratos/contrato.pdf")
            nuevo_contrato = ContratoNuevo.objects.create(
                proveedor_id=contratos[0].proveedor_id,
                contrato="CT-2026-04",
            )
            self.assertGreater(nuevo_contrato.pk, max(registro.pk for registro in registros))

            MigrationExecutor(connection).migrate(old_target)
            reverted_apps = MigrationExecutor(connection).loader.project_state(old_target).apps
            ProveedorRevertido = reverted_apps.get_model("proveedores", "Proveedor")
            revertidos = list(ProveedorRevertido.objects.order_by("id"))
            self.assertEqual(len(revertidos), 4)
            self.assertEqual(revertidos[0].proveedor, "Servicios del Norte")
            self.assertEqual(revertidos[0].documento_pdf.name, "proveedores/contratos/contrato.pdf")
        finally:
            MigrationExecutor(connection).migrate(targets)


class ProveedorPermissionTests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)
        media_settings = override_settings(MEDIA_ROOT=self.media_dir.name)
        media_settings.enable()
        self.addCleanup(media_settings.disable)
        self.client = APIClient()
        self.url = "/api/contratos/"
        self.proveedores_url = "/api/proveedores/"
        self.proveedor = Proveedor.objects.create(codigo="PR-001", nombre="Servicios del Norte")
        self.consulta = User.objects.create_user(username="consulta", password="test-password")
        self.consulta.groups.add(Group.objects.get(name="Consulta"))
        self.administrador = User.objects.create_user(username="admin", password="test-password")
        self.administrador.groups.add(Group.objects.get(name="Administradores"))

    def test_anonymous_user_cannot_read_proveedores(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.get(self.proveedores_url).status_code, 403)

    def test_consulta_role_can_read_but_cannot_create(self):
        self.client.force_authenticate(self.consulta)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        contrato = Contrato.objects.create(
            proveedor=self.proveedor,
            contrato="CT-2026-01",
            tarifa_mensual="250.00",
            tarifa_trimestral="700.00",
            tarifa_semestral="1300.00",
            tarifa_anual="2400.00",
            servicios="Soporte técnico",
        )
        response = self.client.post(
            self.url,
            {
                "proveedor_id": str(self.proveedor.pk),
                "contrato": "CT-2026-01",
                "tarifa_mensual": "250.00",
                "tarifa_trimestral": "700.00",
                "tarifa_semestral": "1300.00",
                "tarifa_anual": "2400.00",
                "servicios": "Soporte técnico",
                "estado": "Activo",
            },
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            self.client.post(
                self.proveedores_url,
                {"codigo": "PR-002", "nombre": "Otro proveedor"},
                format="json",
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.patch(
                f"{self.url}{contrato.pk}/",
                {"estado": "Inactivo"},
                format="json",
            ).status_code,
            403,
        )
        self.assertEqual(self.client.delete(f"{self.url}{contrato.pk}/").status_code, 403)
        self.assertEqual(self.client.delete(f"{self.proveedores_url}{self.proveedor.pk}/").status_code, 403)

    def test_admin_can_delete_supplier_without_contracts(self):
        self.client.force_authenticate(self.administrador)

        response = self.client.delete(f"{self.proveedores_url}{self.proveedor.pk}/")

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Proveedor.objects.filter(pk=self.proveedor.pk).exists())

    def test_admin_cannot_delete_supplier_with_contracts(self):
        Contrato.objects.create(proveedor=self.proveedor, contrato="CT-2026-01")
        self.client.force_authenticate(self.administrador)

        response = self.client.delete(f"{self.proveedores_url}{self.proveedor.pk}/")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.data["detail"],
            "No se puede eliminar este proveedor porque tiene contratos asociados.",
        )
        self.assertTrue(Proveedor.objects.filter(pk=self.proveedor.pk).exists())

    def test_administradores_role_can_create_edit_and_delete(self):
        self.client.force_authenticate(self.administrador)
        response = self.client.post(
            self.url,
            {
                "nuevo_proveedor": '{"codigo":"PR-002","nombre":"Otro proveedor"}',
                "contrato": "CT-2026-01",
                "tarifa_mensual": "250.00",
                "tarifa_trimestral": "700.00",
                "tarifa_semestral": "1300.00",
                "tarifa_anual": "2400.00",
                "servicios": "Soporte técnico",
                "estado": "Activo",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["proveedor"]["codigo"], "PR-002")
        self.assertEqual(response.data["proveedor"]["nombre"], "Otro proveedor")
        self.assertEqual(Proveedor.objects.count(), 2)
        segundo_contrato = self.client.post(
            self.url,
            {
                "proveedor_id": str(response.data["proveedor"]["id"]),
                "contrato": "CT-2026-02",
            },
            format="multipart",
        )
        self.assertEqual(segundo_contrato.status_code, 201)
        self.assertEqual(segundo_contrato.data["proveedor"]["id"], response.data["proveedor"]["id"])
        self.assertEqual(response.data["tarifa_trimestral"], "700.00")
        self.assertEqual(response.data["tarifa_semestral"], "1300.00")
        self.assertEqual(response.data["tarifa_anual"], "2400.00")
        proveedor_url = f"{self.url}{response.data['id']}/"
        self.assertEqual(
            self.client.patch(proveedor_url, {"estado": "Inactivo"}, format="json").status_code,
            200,
        )
        self.assertEqual(self.client.delete(proveedor_url).status_code, 204)

    def test_admin_can_create_proveedor_without_optional_fields(self):
        self.client.force_authenticate(self.administrador)
        response = self.client.post(
            self.url,
            {"proveedor_id": str(self.proveedor.pk)},
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["contrato"], "")
        self.assertEqual(response.data["servicios"], "")
        for tarifa in (
            "tarifa_mensual",
            "tarifa_trimestral",
            "tarifa_semestral",
            "tarifa_anual",
        ):
            self.assertEqual(response.data[tarifa], "0.00")

    def test_new_supplier_code_must_be_unique(self):
        self.client.force_authenticate(self.administrador)
        response = self.client.post(
            self.url,
            {
                "nuevo_proveedor": '{"codigo":"PR-001","nombre":"Otro proveedor"}',
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Proveedor.objects.count(), 1)
        self.assertFalse(Contrato.objects.exists())

    def test_contract_modal_can_assign_code_to_existing_supplier(self):
        self.client.force_authenticate(self.administrador)
        response = self.client.post(
            self.url,
            {
                "proveedor_id": str(self.proveedor.pk),
                "proveedor_codigo": "PR-UPDATED",
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        self.proveedor.refresh_from_db()
        self.assertEqual(self.proveedor.codigo, "PR-UPDATED")

    def test_existing_supplier_code_cannot_duplicate_another_supplier(self):
        otro_proveedor = Proveedor.objects.create(codigo="PR-002", nombre="Otro proveedor")
        self.client.force_authenticate(self.administrador)
        response = self.client.post(
            self.url,
            {
                "proveedor_id": str(self.proveedor.pk),
                "proveedor_codigo": otro_proveedor.codigo,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("proveedor_codigo", response.data)
        self.assertFalse(Contrato.objects.exists())

    def test_blank_tariffs_are_saved_as_zero(self):
        self.client.force_authenticate(self.administrador)
        response = self.client.post(
            self.url,
            {
                "proveedor_id": str(self.proveedor.pk),
                "tarifa_mensual": "",
                "tarifa_trimestral": "",
                "tarifa_semestral": "",
                "tarifa_anual": "",
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["tarifa_mensual"], "0.00")
        self.assertEqual(response.data["tarifa_trimestral"], "0.00")
        self.assertEqual(response.data["tarifa_semestral"], "0.00")
        self.assertEqual(response.data["tarifa_anual"], "0.00")

    def test_admin_can_attach_and_download_a_pdf(self):
        self.client.force_authenticate(self.administrador)
        response = self.client.post(
            self.url,
            {
                "proveedor_id": str(self.proveedor.pk),
                "contrato": "CT-2026-01",
                "tarifa_mensual": "250.00",
                "tarifa_trimestral": "700.00",
                "tarifa_semestral": "1300.00",
                "tarifa_anual": "2400.00",
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
                "proveedor_id": str(self.proveedor.pk),
                "contrato": "CT-2026-01",
                "tarifa_mensual": "250.00",
                "tarifa_trimestral": "700.00",
                "tarifa_semestral": "1300.00",
                "tarifa_anual": "2400.00",
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
        self.assertFalse(Contrato.objects.exists())

    def test_pdf_download_requires_an_authenticated_user(self):
        self.client.force_authenticate(self.administrador)
        response = self.client.post(
            self.url,
            {
                "proveedor_id": str(self.proveedor.pk),
                "contrato": "CT-2026-01",
                "tarifa_mensual": "250.00",
                "tarifa_trimestral": "700.00",
                "tarifa_semestral": "1300.00",
                "tarifa_anual": "2400.00",
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


class RegistroAuditoriaTests(TestCase):
    def setUp(self):
        administradores = Group.objects.get(name="Administradores")
        consulta = Group.objects.get(name="Consulta")
        self.admin = User.objects.create_user(username="admin", password="test-password")
        self.admin.groups.add(administradores)
        self.usuario = User.objects.create_user(username="consulta", password="test-password")
        self.usuario.groups.add(consulta)

    def test_only_administrators_can_read_audit_records(self):
        RegistroAuditoria.objects.create(
            usuario=self.usuario,
            nombre_usuario=self.usuario.username,
            metodo="GET",
            ruta="/api/proveedores/",
            codigo_estado=200,
        )
        client = Client()

        client.force_login(self.usuario)
        self.assertEqual(client.get("/api/auditoria/").status_code, 403)
        self.assertTrue(
            RegistroAuditoria.objects.filter(
                nombre_usuario="consulta",
                ruta="/api/auditoria/",
                codigo_estado=403,
            ).exists()
        )

        client.force_login(self.admin)
        response = client.get("/api/auditoria/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 2)
        self.assertEqual(response.json()["results"][0]["nombre_usuario"], "consulta")

    def test_api_requests_and_session_actions_are_recorded(self):
        client = Client()
        login_response = client.post(
            "/api/auth/login/",
            data=json.dumps({"username": "consulta", "password": "test-password"}),
            content_type="application/json",
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertTrue(
            RegistroAuditoria.objects.filter(
                nombre_usuario="consulta",
                metodo="POST",
                ruta="/api/auth/login/",
                codigo_estado=200,
            ).exists()
        )

        self.assertEqual(client.get("/api/proveedores/").status_code, 200)
        self.assertTrue(
            RegistroAuditoria.objects.filter(
                nombre_usuario="consulta",
                metodo="GET",
                ruta="/api/proveedores/",
                codigo_estado=200,
            ).exists()
        )

        self.assertEqual(client.post("/api/auth/logout/").status_code, 200)
        self.assertTrue(
            RegistroAuditoria.objects.filter(
                nombre_usuario="consulta",
                metodo="POST",
                ruta="/api/auth/logout/",
                codigo_estado=200,
            ).exists()
        )

    def test_reading_audit_does_not_create_more_audit_records(self):
        client = Client()
        client.force_login(self.admin)

        self.assertEqual(client.get("/api/auditoria/").status_code, 200)

        self.assertFalse(RegistroAuditoria.objects.exists())


class DescripcionAuditoriaTests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)
        media_settings = override_settings(MEDIA_ROOT=self.media_dir.name)
        media_settings.enable()
        self.addCleanup(media_settings.disable)
        self.admin = User.objects.create_user(username="admin", password="test-password")
        self.admin.groups.add(Group.objects.get(name="Administradores"))
        self.consulta = User.objects.create_user(username="consulta", password="test-password")
        self.consulta.groups.add(Group.objects.get(name="Consulta"))
        self.client = APIClient()
        self.client.force_login(self.admin)

    def ultimo_registro(self):
        return RegistroAuditoria.objects.order_by("-id").first()

    def test_creating_contract_with_new_supplier_is_described(self):
        response = self.client.post(
            "/api/contratos/",
            {
                "nuevo_proveedor": '{"codigo":"PR-002","nombre":"Otro proveedor"}',
                "contrato": "CT-2026-01",
            },
        )

        self.assertEqual(response.status_code, 201)
        registro = self.ultimo_registro()
        self.assertEqual(registro.accion, RegistroAuditoria.Accion.CREACION)
        self.assertEqual(
            registro.descripcion,
            "Creó el proveedor «Otro proveedor» (PR-002) con el contrato «CT-2026-01»",
        )

    def test_creating_contract_for_existing_supplier_is_described(self):
        proveedor = Proveedor.objects.create(nombre="Servicios del Norte")

        response = self.client.post(
            "/api/contratos/",
            {"proveedor_id": str(proveedor.pk), "contrato": "CT-2026-02"},
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            self.ultimo_registro().descripcion,
            "Creó el contrato «CT-2026-02» del proveedor «Servicios del Norte»",
        )

    def test_updating_contract_lists_changed_fields(self):
        proveedor = Proveedor.objects.create(nombre="Servicios del Norte")
        contrato = Contrato.objects.create(proveedor=proveedor, contrato="CT-1", tarifa_mensual="100.00")

        response = self.client.patch(
            f"/api/contratos/{contrato.pk}/",
            {"estado": "Inactivo", "tarifa_mensual": "120.00", "servicios": "Soporte"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        registro = self.ultimo_registro()
        self.assertEqual(registro.accion, RegistroAuditoria.Accion.ACTUALIZACION)
        self.assertEqual(
            registro.descripcion,
            "Actualizó el contrato «CT-1» del proveedor «Servicios del Norte». "
            "Cambios: tarifa mensual: 100.00 → 120.00; estado: Activo → Inactivo; servicios",
        )

    def test_deleting_supplier_and_contract_is_described(self):
        proveedor = Proveedor.objects.create(codigo="PR-9", nombre="Servicios del Norte")
        contrato = Contrato.objects.create(proveedor=proveedor, contrato="CT-1")

        self.assertEqual(self.client.delete(f"/api/proveedores/{proveedor.pk}/").status_code, 409)
        self.assertEqual(
            self.ultimo_registro().descripcion,
            "Intentó eliminar el proveedor «Servicios del Norte» (PR-9), pero tiene contratos asociados",
        )

        self.assertEqual(self.client.delete(f"/api/contratos/{contrato.pk}/").status_code, 204)
        self.assertEqual(
            self.ultimo_registro().descripcion,
            "Eliminó el contrato «CT-1» del proveedor «Servicios del Norte» (PR-9)",
        )

        self.assertEqual(self.client.delete(f"/api/proveedores/{proveedor.pk}/").status_code, 204)
        registro = self.ultimo_registro()
        self.assertEqual(registro.accion, RegistroAuditoria.Accion.ELIMINACION)
        self.assertEqual(registro.descripcion, "Eliminó el proveedor «Servicios del Norte» (PR-9)")

    def test_generic_descriptions_for_lists_and_rejected_requests(self):
        self.assertEqual(self.client.get("/api/proveedores/").status_code, 200)
        self.assertEqual(self.ultimo_registro().descripcion, "Consultó la lista de proveedores")

        self.client.force_login(self.consulta)
        self.assertEqual(self.client.post("/api/contratos/", {"contrato": "X"}).status_code, 403)
        registro = self.ultimo_registro()
        self.assertEqual(registro.accion, RegistroAuditoria.Accion.CREACION)
        self.assertEqual(registro.descripcion, "Intentó crear un contrato (sin permiso)")

    def test_session_actions_and_api_output_include_description(self):
        client = Client()
        client.post(
            "/api/auth/login/",
            data=json.dumps({"username": "admin", "password": "test-password"}),
            content_type="application/json",
        )
        client.post("/api/auth/logout/")
        self.assertEqual(
            list(RegistroAuditoria.objects.order_by("id").values_list("accion", "descripcion")),
            [("inicio_sesion", "Inició sesión"), ("cierre_sesion", "Cerró sesión")],
        )

        resultado = self.client.get("/api/auditoria/").json()["results"][0]
        self.assertEqual(resultado["accion"], "cierre_sesion")
        self.assertEqual(resultado["accion_display"], "Cierre de sesión")
        self.assertEqual(resultado["descripcion"], "Cerró sesión")


class FiltrosAuditoriaTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="admin", password="test-password")
        self.admin.groups.add(Group.objects.get(name="Administradores"))
        for nombre, accion in [
            ("ana", "creacion"),
            ("ana", "consulta"),
            ("luis", "creacion"),
            ("luis", "eliminacion"),
        ]:
            RegistroAuditoria.objects.create(
                nombre_usuario=nombre,
                accion=accion,
                metodo="GET",
                ruta="/api/contratos/",
                codigo_estado=200,
            )
        self.client = Client()
        self.client.force_login(self.admin)

    def nombres_y_acciones(self, query):
        response = self.client.get(f"/api/auditoria/{query}")
        self.assertEqual(response.status_code, 200)
        return sorted((r["nombre_usuario"], r["accion"]) for r in response.json()["results"])

    def test_filters_by_user_and_action(self):
        self.assertEqual(
            self.nombres_y_acciones("?usuario=ana"),
            [("ana", "consulta"), ("ana", "creacion")],
        )
        self.assertEqual(
            self.nombres_y_acciones("?accion=creacion"),
            [("ana", "creacion"), ("luis", "creacion")],
        )
        self.assertEqual(self.nombres_y_acciones("?usuario=luis&accion=creacion"), [("luis", "creacion")])
        self.assertEqual(len(self.nombres_y_acciones("")), 4)

    def test_lists_distinct_users_for_the_filter(self):
        response = self.client.get("/api/auditoria/usuarios/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), ["ana", "luis"])
        self.assertEqual(RegistroAuditoria.objects.count(), 4)

    def test_users_list_is_only_for_administrators(self):
        consulta = User.objects.create_user(username="consulta", password="test-password")
        consulta.groups.add(Group.objects.get(name="Consulta"))
        self.client.force_login(consulta)
        self.assertEqual(self.client.get("/api/auditoria/usuarios/").status_code, 403)
