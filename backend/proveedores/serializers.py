from pathlib import PurePosixPath

from rest_framework import serializers

from .models import Proveedor


class ProveedorSerializer(serializers.ModelSerializer):
    archivo_pdf = serializers.FileField(
        source="documento_pdf",
        write_only=True,
        required=False,
    )
    tiene_pdf = serializers.SerializerMethodField()
    pdf_url = serializers.SerializerMethodField()

    class Meta:
        model = Proveedor
        fields = [
            "id",
            "proveedor",
            "contrato",
            "tarifa_mensual",
            "servicios",
            "estado",
            "archivo_pdf",
            "tiene_pdf",
            "pdf_url",
        ]

    def validate_archivo_pdf(self, archivo):
        if archivo.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("El PDF no puede superar los 10 MB.")
        if PurePosixPath(archivo.name).suffix.lower() != ".pdf":
            raise serializers.ValidationError("Adjunta un archivo con extensión .pdf.")
        if archivo.read(5) != b"%PDF-":
            raise serializers.ValidationError("El archivo seleccionado no parece ser un PDF válido.")
        archivo.seek(0)
        return archivo

    def get_tiene_pdf(self, proveedor):
        return bool(proveedor.documento_pdf)

    def get_pdf_url(self, proveedor):
        if not proveedor.documento_pdf:
            return None
        request = self.context.get("request")
        path = f"/api/proveedores/{proveedor.pk}/pdf/"
        return request.build_absolute_uri(path) if request else path
