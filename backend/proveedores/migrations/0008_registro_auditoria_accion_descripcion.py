from django.db import migrations, models

from proveedores.auditoria import accion_para, descripcion_generica


def completar_registros_existentes(apps, schema_editor):
    RegistroAuditoria = apps.get_model("proveedores", "RegistroAuditoria")
    for registro in RegistroAuditoria.objects.all().iterator():
        registro.accion = accion_para(registro.metodo, registro.ruta)
        registro.descripcion = descripcion_generica(
            registro.metodo, registro.ruta, registro.codigo_estado
        )[:500]
        registro.save(update_fields=["accion", "descripcion"])


class Migration(migrations.Migration):
    dependencies = [
        ("proveedores", "0007_registro_auditoria"),
    ]

    operations = [
        migrations.AddField(
            model_name="registroauditoria",
            name="accion",
            field=models.CharField(
                choices=[
                    ("inicio_sesion", "Inicio de sesión"),
                    ("cierre_sesion", "Cierre de sesión"),
                    ("consulta", "Consulta"),
                    ("creacion", "Creación"),
                    ("actualizacion", "Actualización"),
                    ("eliminacion", "Eliminación"),
                    ("otro", "Otro"),
                ],
                default="otro",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="registroauditoria",
            name="descripcion",
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.RunPython(completar_registros_existentes, migrations.RunPython.noop),
    ]
