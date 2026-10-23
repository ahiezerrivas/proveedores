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


class RegistroAuditoria(models.Model):
    class Accion(models.TextChoices):
        INICIO_SESION = "inicio_sesion", "Inicio de sesión"
        CIERRE_SESION = "cierre_sesion", "Cierre de sesión"
        CONSULTA = "consulta", "Consulta"
        CREACION = "creacion", "Creación"
        ACTUALIZACION = "actualizacion", "Actualización"
        ELIMINACION = "eliminacion", "Eliminación"
        OTRO = "otro", "Otro"

    usuario = models.ForeignKey(
        "auth.User",
        related_name="registros_auditoria",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    nombre_usuario = models.CharField(max_length=150)
    accion = models.CharField(max_length=20, choices=Accion.choices, default=Accion.OTRO)
    descripcion = models.CharField(max_length=500, blank=True)
    metodo = models.CharField(max_length=10)
    ruta = models.CharField(max_length=255)
    codigo_estado = models.PositiveSmallIntegerField()
    direccion_ip = models.GenericIPAddressField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-fecha", "-id"]

    def __str__(self):
        return f"{self.nombre_usuario} — {self.descripcion or f'{self.metodo} {self.ruta}'}"
