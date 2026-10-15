from django.core.validators import MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("proveedores", "0003_proveedor_documento_pdf"),
    ]

    operations = [
        migrations.AddField(
            model_name="proveedor",
            name="tarifa_trimestral",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                max_digits=12,
                validators=[MinValueValidator(0)],
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="proveedor",
            name="tarifa_semestral",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                max_digits=12,
                validators=[MinValueValidator(0)],
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="proveedor",
            name="tarifa_anual",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                max_digits=12,
                validators=[MinValueValidator(0)],
            ),
            preserve_default=False,
        ),
    ]
