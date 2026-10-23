from django.http import FileResponse
from django.db.models.deletion import ProtectedError
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.response import Response

from .models import Contrato, Proveedor, RegistroAuditoria
from .serializers import ContratoSerializer, ProveedorSerializer, RegistroAuditoriaSerializer


class EsAdministradorOConsulta(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_superuser or request.user.groups.filter(
            name="Administradores"
        ).exists()


class EsAdministrador(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_superuser
            or request.user.groups.filter(name="Administradores").exists()
        )


class ProveedorViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    permission_classes = [EsAdministradorOConsulta]

    def destroy(self, request, *args, **kwargs):
        proveedor = self.get_object()
        if proveedor.contratos.exists():
            return Response(
                {"detail": "No se puede eliminar este proveedor porque tiene contratos asociados."},
                status=status.HTTP_409_CONFLICT,
            )
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": "No se puede eliminar este proveedor porque tiene contratos asociados."},
                status=status.HTTP_409_CONFLICT,
            )


class ContratoViewSet(viewsets.ModelViewSet):
    queryset = Contrato.objects.select_related("proveedor").all()
    serializer_class = ContratoSerializer
    permission_classes = [EsAdministradorOConsulta]

    def perform_update(self, serializer):
        old_name = serializer.instance.documento_pdf.name
        contrato = serializer.save()
        if old_name and old_name != contrato.documento_pdf.name:
            contrato.documento_pdf.storage.delete(old_name)

    def perform_destroy(self, instance):
        documento = instance.documento_pdf
        instance.delete()
        if documento:
            documento.storage.delete(documento.name)

    @action(detail=True, methods=["get", "delete"], url_path="pdf")
    def pdf(self, request, pk=None):
        contrato = self.get_object()
        if request.method == "DELETE":
            if not contrato.documento_pdf:
                return Response(status=status.HTTP_404_NOT_FOUND)
            documento = contrato.documento_pdf
            contrato.documento_pdf = ""
            contrato.save(update_fields=["documento_pdf"])
            documento.storage.delete(documento.name)
            return Response(status=status.HTTP_204_NO_CONTENT)

        if not contrato.documento_pdf:
            return Response({"detail": "Este proveedor no tiene un PDF adjunto."}, status=status.HTTP_404_NOT_FOUND)
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
    permission_classes = [EsAdministrador]
    pagination_class = AuditoriaPaginacion
