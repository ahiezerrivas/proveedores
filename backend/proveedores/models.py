from django.db import models
from django.core.validators import MinValueValidator


class Proveedor(models.Model):
    class Estado(models.TextChoices):
        ACTIVO = "Activo", "Activo"
        PENDIENTE = "Pendiente", "Pendiente"
        INACTIVO = "Inactivo", "Inactivo"

    proveedor = models.CharField(max_length=200)
    contrato = models.CharField(max_length=120)
    tarifa_mensual = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    servicios = models.TextField()
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.ACTIVO)
    documento_pdf = models.FileField(
        upload_to="proveedores/contratos/",
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["proveedor"]

    def __str__(self):
        return f"{self.proveedor} — {self.contrato}"
