from django.contrib import admin

from .models import Contrato, Proveedor


class ContratoInline(admin.TabularInline):
    model = Contrato
    extra = 0


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre")
    search_fields = ("codigo", "nombre")
    inlines = (ContratoInline,)


@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display = (
        "proveedor",
        "contrato",
        "tarifa_mensual",
        "tarifa_trimestral",
        "tarifa_semestral",
        "tarifa_anual",
        "estado",
    )
    list_filter = ("estado",)
    search_fields = ("proveedor__codigo", "proveedor__nombre", "contrato", "servicios")
