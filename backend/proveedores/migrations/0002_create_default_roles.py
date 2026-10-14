from django.db import migrations


def create_default_roles(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    database = schema_editor.connection.alias
    Group.objects.using(database).get_or_create(name="Administradores")
    Group.objects.using(database).get_or_create(name="Consulta")


def remove_default_roles(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    database = schema_editor.connection.alias
    Group.objects.using(database).filter(
        name__in=["Administradores", "Consulta"]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("proveedores", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_default_roles, remove_default_roles),
    ]
