from pathlib import PurePosixPath

from django.db import transaction
from rest_framework import serializers

from .models import Contrato, Proveedor


class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedor
        fields = ["id", "codigo", "nombre"]


class ContratoSerializer(serializers.ModelSerializer):
    TARIFAS = (
        "tarifa_mensual",
        "tarifa_trimestral",
        "tarifa_semestral",
        "tarifa_anual",
    )

    archivo_pdf = serializers.FileField(
        source="documento_pdf",
        write_only=True,
        required=False,
    )
    proveedor = ProveedorSerializer(read_only=True)
    proveedor_id = serializers.PrimaryKeyRelatedField(
        source="proveedor",
        queryset=Proveedor.objects.all(),
        write_only=True,
        required=False,
    )
    proveedor_codigo = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        max_length=60,
    )
    nuevo_proveedor = serializers.JSONField(write_only=True, required=False)
    tiene_pdf = serializers.SerializerMethodField()
    pdf_url = serializers.SerializerMethodField()

    class Meta:
        model = Contrato
        fields = [
            "id",
            "proveedor",
            "proveedor_id",
            "proveedor_codigo",
            "nuevo_proveedor",
            "contrato",
            "tarifa_mensual",
            "tarifa_trimestral",
            "tarifa_semestral",
            "tarifa_anual",
            "servicios",
            "estado",
            "archivo_pdf",
            "tiene_pdf",
            "pdf_url",
        ]

    def validate_nuevo_proveedor(self, datos):
        serializer = ProveedorSerializer(data=datos)
        serializer.is_valid(raise_exception=True)
        proveedor = serializer.validated_data
        codigo = proveedor.get("codigo", "").strip()
        nombre = proveedor.get("nombre", "").strip()
        if codigo and Proveedor.objects.filter(codigo=codigo).exists():
            raise serializers.ValidationError(
                {"codigo": "Ya existe un proveedor con este código; selecciónalo en la lista."}
            )
        if not codigo and Proveedor.objects.filter(nombre=nombre).exists():
            raise serializers.ValidationError(
                {"nombre": "Ya existe un proveedor con este nombre; selecciónalo en la lista."}
            )
        proveedor["codigo"] = codigo
        proveedor["nombre"] = nombre
        return proveedor

    def validate(self, attrs):
        tiene_proveedor = "proveedor" in attrs
        tiene_nuevo_proveedor = "nuevo_proveedor" in attrs
        if "proveedor_codigo" in attrs:
            proveedor = attrs.get("proveedor") or (
                self.instance.proveedor if self.instance else None
            )
            if proveedor is None:
                raise serializers.ValidationError(
                    {"proveedor_id": "Selecciona un proveedor antes de indicar su código."}
                )
            codigo = attrs["proveedor_codigo"].strip()
            if codigo and Proveedor.objects.filter(codigo=codigo).exclude(pk=proveedor.pk).exists():
                raise serializers.ValidationError(
                    {"proveedor_codigo": "Ya existe un proveedor con este código."}
                )
            attrs["proveedor_codigo"] = codigo
        if tiene_proveedor and tiene_nuevo_proveedor:
            raise serializers.ValidationError(
                "Selecciona un proveedor existente o registra uno nuevo, no ambos."
            )
        if not self.instance and not (tiene_proveedor or tiene_nuevo_proveedor):
            raise serializers.ValidationError(
                {"proveedor_id": "Selecciona un proveedor o registra uno nuevo."}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        datos_proveedor = validated_data.pop("nuevo_proveedor", None)
        codigo_proveedor = validated_data.pop("proveedor_codigo", None)
        if datos_proveedor is not None:
            validated_data["proveedor"] = Proveedor.objects.create(**datos_proveedor)
        elif codigo_proveedor is not None:
            validated_data["proveedor"].codigo = codigo_proveedor
            validated_data["proveedor"].save(update_fields=["codigo"])
        return super().create(validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        datos_proveedor = validated_data.pop("nuevo_proveedor", None)
        codigo_proveedor = validated_data.pop("proveedor_codigo", None)
        if datos_proveedor is not None:
            validated_data["proveedor"] = Proveedor.objects.create(**datos_proveedor)
        elif codigo_proveedor is not None:
            proveedor = validated_data.get("proveedor", instance.proveedor)
            proveedor.codigo = codigo_proveedor
            proveedor.save(update_fields=["codigo"])
        return super().update(instance, validated_data)

    def to_internal_value(self, data):
        data = data.copy()
        for tarifa in self.TARIFAS:
            valor = data.get(tarifa)
            if isinstance(valor, str) and not valor.strip():
                data[tarifa] = 0
        return super().to_internal_value(data)

    def validate_archivo_pdf(self, archivo):
        if archivo.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("El PDF no puede superar los 10 MB.")
        if PurePosixPath(archivo.name).suffix.lower() != ".pdf":
            raise serializers.ValidationError("Adjunta un archivo con extensión .pdf.")
        if archivo.read(5) != b"%PDF-":
            raise serializers.ValidationError("El archivo seleccionado no parece ser un PDF válido.")
        archivo.seek(0)
        return archivo

    def get_tiene_pdf(self, contrato):
        return bool(contrato.documento_pdf)

    def get_pdf_url(self, contrato):
        if not contrato.documento_pdf:
            return None
        request = self.context.get("request")
        path = f"/api/contratos/{contrato.pk}/pdf/"
        return request.build_absolute_uri(path) if request else path
