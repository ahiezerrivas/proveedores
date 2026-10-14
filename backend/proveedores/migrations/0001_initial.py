import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Proveedor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("proveedor", models.CharField(max_length=200)),
                ("contrato", models.CharField(max_length=120)),
                ("tarifa_mensual", models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(0)])),
                ("servicios", models.TextField()),
                ("estado", models.CharField(choices=[("Activo", "Activo"), ("Pendiente", "Pendiente"), ("Inactivo", "Inactivo")], default="Activo", max_length=12)),
            ],
            options={"ordering": ["proveedor"]},
        ),
    ]
