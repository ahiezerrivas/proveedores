from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("proveedores", "0002_create_default_roles"),
    ]

    operations = [
        migrations.AddField(
            model_name="proveedor",
            name="documento_pdf",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="proveedores/contratos/",
            ),
        ),
    ]
