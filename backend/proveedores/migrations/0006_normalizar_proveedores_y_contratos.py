import django.core.validators
import django.db.models
from django.core.management.color import no_style
from django.db import migrations, models


def migrar_proveedores_y_contratos(apps, schema_editor):
    ProveedorAnterior = apps.get_model("proveedores", "ContratoLegacy")
    Proveedor = apps.get_model("proveedores", "Proveedor")
    Contrato = apps.get_model("proveedores", "Contrato")
    base_datos = schema_editor.connection.alias
    proveedores = {}

    for anterior in ProveedorAnterior.objects.using(base_datos).all().iterator():
        nombre = anterior.proveedor
        if nombre not in proveedores:
            proveedor = Proveedor.objects.using(base_datos).create(
                codigo="",
                nombre=nombre,
            )
            proveedores[nombre] = proveedor.pk

        Contrato.objects.using(base_datos).create(
            id=anterior.pk,
            proveedor_id=proveedores[nombre],
            contrato=anterior.contrato,
            tarifa_mensual=anterior.tarifa_mensual,
            tarifa_trimestral=anterior.tarifa_trimestral,
            tarifa_semestral=anterior.tarifa_semestral,
            tarifa_anual=anterior.tarifa_anual,
            servicios=anterior.servicios,
            estado=anterior.estado,
            documento_pdf=anterior.documento_pdf.name,
        )

    with schema_editor.connection.cursor() as cursor:
        for statement in schema_editor.connection.ops.sequence_reset_sql(
            no_style(),
            [Contrato],
        ):
            cursor.execute(statement)


def revertir_proveedores_y_contratos(apps, schema_editor):
    ProveedorAnterior = apps.get_model("proveedores", "ContratoLegacy")
    Proveedor = apps.get_model("proveedores", "Proveedor")
    Contrato = apps.get_model("proveedores", "Contrato")
    base_datos = schema_editor.connection.alias
    nombres = dict(
        Proveedor.objects.using(base_datos).values_list("pk", "nombre")
    )

    ProveedorAnterior.objects.using(base_datos).bulk_create(
        [
            ProveedorAnterior(
                id=contrato.pk,
                proveedor=nombres[contrato.proveedor_id],
                contrato=contrato.contrato,
                tarifa_mensual=contrato.tarifa_mensual,
                tarifa_trimestral=contrato.tarifa_trimestral,
                tarifa_semestral=contrato.tarifa_semestral,
                tarifa_anual=contrato.tarifa_anual,
                servicios=contrato.servicios,
                estado=contrato.estado,
                documento_pdf=contrato.documento_pdf.name,
            )
            for contrato in Contrato.objects.using(base_datos).all().iterator()
        ]
    )
    with schema_editor.connection.cursor() as cursor:
        for statement in schema_editor.connection.ops.sequence_reset_sql(
            no_style(),
            [ProveedorAnterior],
        ):
            cursor.execute(statement)


class Migration(migrations.Migration):
    dependencies = [
        ("proveedores", "0005_proveedor_campos_opcionales"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="Proveedor",
            new_name="ContratoLegacy",
        ),
        migrations.CreateModel(
            name="Proveedor",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("codigo", models.CharField(blank=True, default="", max_length=60)),
                ("nombre", models.CharField(blank=True, max_length=200)),
            ],
            options={"ordering": ["nombre"]},
        ),
        migrations.AddConstraint(
            model_name="proveedor",
            constraint=models.UniqueConstraint(
                condition=~django.db.models.Q(codigo=""),
                fields=("codigo",),
                name="proveedor_codigo_unico_no_vacio",
            ),
        ),
        migrations.CreateModel(
            name="Contrato",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("contrato", models.CharField(blank=True, max_length=120)),
                (
                    "tarifa_mensual",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(0)],
                    ),
                ),
                (
                    "tarifa_trimestral",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(0)],
                    ),
                ),
                (
                    "tarifa_semestral",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(0)],
                    ),
                ),
                (
                    "tarifa_anual",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(0)],
                    ),
                ),
                ("servicios", models.TextField(blank=True)),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("Activo", "Activo"),
                            ("Pendiente", "Pendiente"),
                            ("Inactivo", "Inactivo"),
                        ],
                        default="Activo",
                        max_length=12,
                    ),
                ),
                (
                    "documento_pdf",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to="proveedores/contratos/",
                    ),
                ),
                (
                    "proveedor",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="contratos",
                        to="proveedores.proveedor",
                    ),
                ),
            ],
            options={"ordering": ["proveedor__nombre", "contrato"]},
        ),
        migrations.RunPython(
            migrar_proveedores_y_contratos,
            revertir_proveedores_y_contratos,
        ),
        migrations.AlterField(
            model_name="contrato",
            name="proveedor",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="contratos",
                to="proveedores.proveedor",
            ),
        ),
        migrations.DeleteModel(name="ContratoLegacy"),
    ]
