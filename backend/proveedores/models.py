from django.core.validators import MinValueValidator
from django.db import models


class Proveedor(models.Model):
    codigo = models.CharField(max_length=60, blank=True, default="")
    nombre = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["codigo"],
                condition=~models.Q(codigo=""),
                name="proveedor_codigo_unico_no_vacio",
            ),
        ]

    def __str__(self):
        return f"{self.codigo} — {self.nombre}" if self.codigo else self.nombre


class Contrato(models.Model):
    class Estado(models.TextChoices):
        ACTIVO = "Activo", "Activo"
        PENDIENTE = "Pendiente", "Pendiente"
        INACTIVO = "Inactivo", "Inactivo"

    proveedor = models.ForeignKey(
        Proveedor,
        related_name="contratos",
        on_delete=models.PROTECT,
    )
    contrato = models.CharField(max_length=120, blank=True)
    tarifa_mensual = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    tarifa_trimestral = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    tarifa_semestral = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    tarifa_anual = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    servicios = models.TextField(blank=True)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.ACTIVO)
    documento_pdf = models.FileField(
        upload_to="proveedores/contratos/",
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["proveedor__nombre", "contrato"]

    def __str__(self):
        return f"{self.proveedor.nombre} — {self.contrato}"
