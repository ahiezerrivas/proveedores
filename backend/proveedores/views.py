from django.http import FileResponse
from django.db.models.deletion import ProtectedError
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.response import Response

from .auditoria import describir, nombre_contrato, nombre_proveedor
from .models import Contrato, Proveedor, RegistroAuditoria
from .serializers import ContratoSerializer, ProveedorSerializer, RegistroAuditoriaSerializer


class PermisosDelModelo(DjangoModelPermissions):
    """Usa los permisos de Django (ver/agregar/cambiar/eliminar) asignados a usuarios y grupos."""

    perms_map = {
        "GET": ["%(app_label)s.view_%(model_name)s"],
        "HEAD": ["%(app_label)s.view_%(model_name)s"],
        "OPTIONS": [],
        "POST": ["%(app_label)s.add_%(model_name)s"],
        "PUT": ["%(app_label)s.change_%(model_name)s"],
        "PATCH": ["%(app_label)s.change_%(model_name)s"],
        "DELETE": ["%(app_label)s.delete_%(model_name)s"],
    }


class PermisosPdfContrato(PermisosDelModelo):
    perms_map = {
        **PermisosDelModelo.perms_map,
        "DELETE": ["%(app_label)s.change_%(model_name)s"],
    }


class ProveedorViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    permission_classes = [PermisosDelModelo]

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        describir(request, f"Consultó el proveedor {nombre_proveedor(self.get_object())}")
        return response

    def destroy(self, request, *args, **kwargs):
        proveedor = self.get_object()
        nombre = nombre_proveedor(proveedor)
        conflicto = Response(
            {"detail": "No se puede eliminar este proveedor porque tiene contratos asociados."},
            status=status.HTTP_409_CONFLICT,
        )
        if proveedor.contratos.exists():
            describir(request, f"Intentó eliminar el proveedor {nombre}, pero tiene contratos asociados")
            return conflicto
        try:
            response = super().destroy(request, *args, **kwargs)
        except ProtectedError:
            describir(request, f"Intentó eliminar el proveedor {nombre}, pero tiene contratos asociados")
            return conflicto
        describir(request, f"Eliminó el proveedor {nombre}")
        return response


class ContratoViewSet(viewsets.ModelViewSet):
    queryset = Contrato.objects.select_related("proveedor").all()
    serializer_class = ContratoSerializer
    permission_classes = [PermisosDelModelo]

    CAMPOS_AUDITADOS = {
        "contrato": "nombre del contrato",
        "tarifa_mensual": "tarifa mensual",
        "tarifa_trimestral": "tarifa trimestral",
        "tarifa_semestral": "tarifa semestral",
        "tarifa_anual": "tarifa anual",
        "estado": "estado",
    }

    def _valores_auditados(self, contrato):
        valores = {campo: str(getattr(contrato, campo)) for campo in self.CAMPOS_AUDITADOS}
        valores["servicios"] = contrato.servicios
        valores["documento_pdf"] = contrato.documento_pdf.name or ""
        valores["proveedor"] = nombre_proveedor(contrato.proveedor)
        return valores

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        describir(request, f"Consultó el contrato {nombre_contrato(self.get_object())}")
        return response

    def _validar_permisos_proveedor(self, serializer):
        datos = serializer.validated_data
        usuario = self.request.user
        if "nuevo_proveedor" in datos and not usuario.has_perm("proveedores.add_proveedor"):
            raise PermissionDenied("No tienes permiso para registrar proveedores nuevos.")
        if "proveedor_codigo" in datos:
            proveedor = datos.get("proveedor") or getattr(serializer.instance, "proveedor", None)
            if (
                proveedor is not None
                and datos["proveedor_codigo"] != proveedor.codigo
                and not usuario.has_perm("proveedores.change_proveedor")
            ):
                raise PermissionDenied("No tienes permiso para cambiar el código del proveedor.")

    def perform_create(self, serializer):
        self._validar_permisos_proveedor(serializer)
        crea_proveedor = "nuevo_proveedor" in serializer.validated_data
        contrato = serializer.save()
        if crea_proveedor:
            nombre = f"«{contrato.contrato}»" if contrato.contrato else f"#{contrato.pk}"
            descripcion = (
                f"Creó el proveedor {nombre_proveedor(contrato.proveedor)} con el contrato {nombre}"
            )
        else:
            descripcion = f"Creó el contrato {nombre_contrato(contrato)}"
        if contrato.documento_pdf:
            descripcion += " (con PDF adjunto)"
        describir(self.request, descripcion)

    def perform_update(self, serializer):
        self._validar_permisos_proveedor(serializer)
        old_name = serializer.instance.documento_pdf.name
        antes = self._valores_auditados(serializer.instance)
        crea_proveedor = "nuevo_proveedor" in serializer.validated_data
        contrato = serializer.save()
        if old_name and old_name != contrato.documento_pdf.name:
            contrato.documento_pdf.storage.delete(old_name)

        despues = self._valores_auditados(contrato)
        cambios = [
            f"{etiqueta}: {antes[campo] or '—'} → {despues[campo] or '—'}"
            for campo, etiqueta in self.CAMPOS_AUDITADOS.items()
            if antes[campo] != despues[campo]
        ]
        if antes["servicios"] != despues["servicios"]:
            cambios.append("servicios")
        if antes["documento_pdf"] != despues["documento_pdf"]:
            cambios.append("PDF adjunto reemplazado" if old_name else "PDF adjunto agregado")
        if antes["proveedor"] != despues["proveedor"]:
            nuevo = " (nuevo)" if crea_proveedor else ""
            cambios.append(f"proveedor: {antes['proveedor']} → {despues['proveedor']}{nuevo}")
        descripcion = f"Actualizó el contrato {nombre_contrato(contrato)}"
        if cambios:
            descripcion += f". Cambios: {'; '.join(cambios)}"
        describir(self.request, descripcion)

    def perform_destroy(self, instance):
        descripcion = f"Eliminó el contrato {nombre_contrato(instance)}"
        documento = instance.documento_pdf
        instance.delete()
        if documento:
            documento.storage.delete(documento.name)
        describir(self.request, descripcion)

    @action(
        detail=True,
        methods=["get", "delete"],
        url_path="pdf",
        permission_classes=[PermisosPdfContrato],
    )
    def pdf(self, request, pk=None):
        contrato = self.get_object()
        if request.method == "DELETE":
            if not contrato.documento_pdf:
                return Response(status=status.HTTP_404_NOT_FOUND)
            documento = contrato.documento_pdf
            contrato.documento_pdf = ""
            contrato.save(update_fields=["documento_pdf"])
            documento.storage.delete(documento.name)
            describir(request, f"Eliminó el PDF del contrato {nombre_contrato(contrato)}")
            return Response(status=status.HTTP_204_NO_CONTENT)

        if not contrato.documento_pdf:
            return Response({"detail": "Este proveedor no tiene un PDF adjunto."}, status=status.HTTP_404_NOT_FOUND)
        describir(request, f"Abrió el PDF del contrato {nombre_contrato(contrato)}")
        return FileResponse(
            contrato.documento_pdf.open("rb"),
            as_attachment=False,
            filename=f"contrato-{contrato.pk}.pdf",
            content_type="application/pdf",
        )


class AuditoriaPaginacion(PageNumberPagination):
    page_size = 50


class RegistroAuditoriaViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = RegistroAuditoria.objects.all()
    serializer_class = RegistroAuditoriaSerializer
    permission_classes = [PermisosDelModelo]
    pagination_class = AuditoriaPaginacion

    def get_queryset(self):
        queryset = super().get_queryset()
        usuario = self.request.query_params.get("usuario")
        accion = self.request.query_params.get("accion")
        if usuario:
            queryset = queryset.filter(nombre_usuario=usuario)
        if accion:
            queryset = queryset.filter(accion=accion)
        return queryset

    @action(detail=False, methods=["get"], pagination_class=None)
    def usuarios(self, request):
        nombres = (
            RegistroAuditoria.objects.order_by("nombre_usuario")
            .values_list("nombre_usuario", flat=True)
            .distinct()
        )
        return Response(list(nombres))
