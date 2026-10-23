from django.contrib.auth.management import create_permissions
from django.db import migrations

PERMISOS_POR_GRUPO = {
    "Administradores": [
        "view_proveedor",
        "add_proveedor",
        "change_proveedor",
        "delete_proveedor",
        "view_contrato",
        "add_contrato",
        "change_contrato",
        "delete_contrato",
        "view_registroauditoria",
    ],
    "Consulta": ["view_proveedor", "view_contrato"],
}


def asignar_permisos(apps, schema_editor):
    app_config = apps.get_app_config("proveedores")
    app_config.models_module = True
    create_permissions(app_config, apps=apps, verbosity=0)
    app_config.models_module = None

    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    for nombre, codenames in PERMISOS_POR_GRUPO.items():
        grupo, _ = Group.objects.get_or_create(name=nombre)
        grupo.permissions.add(
            *Permission.objects.filter(
                content_type__app_label="proveedores",
                codename__in=codenames,
            )
        )


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
        ("proveedores", "0008_registro_auditoria_accion_descripcion"),
    ]

    operations = [
        migrations.RunPython(asignar_permisos, migrations.RunPython.noop),
    ]
