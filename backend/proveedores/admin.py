from django.contrib import admin

from .models import Proveedor


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ("proveedor", "contrato", "tarifa_mensual", "estado")
    list_filter = ("estado",)
    search_fields = ("proveedor", "contrato", "servicios")
