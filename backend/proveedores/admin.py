from django.contrib import admin

from .models import Contrato, Proveedor, RegistroAuditoria


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


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    list_display = ("fecha", "nombre_usuario", "accion", "descripcion", "codigo_estado", "direccion_ip")
    list_filter = ("accion",)
    search_fields = ("nombre_usuario", "descripcion", "ruta")
    readonly_fields = [field.name for field in RegistroAuditoria._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
