import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("proveedores", "0004_proveedor_tarifas_periodicas"),
    ]

    operations = [
        migrations.AlterField(
            model_name="proveedor",
            name="proveedor",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name="proveedor",
            name="contrato",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AlterField(
            model_name="proveedor",
            name="tarifa_mensual",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                default=0,
                max_digits=12,
                validators=[django.core.validators.MinValueValidator(0)],
            ),
        ),
        migrations.AlterField(
            model_name="proveedor",
            name="tarifa_trimestral",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                default=0,
                max_digits=12,
                validators=[django.core.validators.MinValueValidator(0)],
            ),
        ),
        migrations.AlterField(
            model_name="proveedor",
            name="tarifa_semestral",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                default=0,
                max_digits=12,
                validators=[django.core.validators.MinValueValidator(0)],
            ),
        ),
        migrations.AlterField(
            model_name="proveedor",
            name="tarifa_anual",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                default=0,
                max_digits=12,
                validators=[django.core.validators.MinValueValidator(0)],
            ),
        ),
        migrations.AlterField(
            model_name="proveedor",
            name="servicios",
            field=models.TextField(blank=True),
        ),
    ]
