import re

ACCIONES_POR_METODO = {
    "GET": "consulta",
    "HEAD": "consulta",
    "POST": "creacion",
    "PUT": "actualizacion",
    "PATCH": "actualizacion",
    "DELETE": "eliminacion",
}

VERBOS = {
    "consulta": "Consultó",
    "creacion": "Creó",
    "actualizacion": "Actualizó",
    "eliminacion": "Eliminó",
}

VERBOS_INTENTO = {
    "consulta": "consultar",
    "creacion": "crear",
    "actualizacion": "actualizar",
    "eliminacion": "eliminar",
}

RECURSOS = {
    "proveedores": ("la lista de proveedores", "el proveedor", "un proveedor"),
    "contratos": ("la lista de contratos", "el contrato", "un contrato"),
    "auditoria": ("el registro de auditoría", "el registro de auditoría", "un registro de auditoría"),
}

MOTIVOS = {
    400: "datos inválidos",
    401: "sesión no iniciada",
    403: "sin permiso",
    404: "no encontrado",
    405: "operación no permitida",
    409: "conflicto",
}

RUTA_API = re.compile(r"^/api/(?P<recurso>[\w-]+)/(?:(?P<pk>\d+)/)?(?:(?P<extra>[\w-]+)/)?$")


def accion_para(metodo, ruta):
    if ruta == "/api/auth/login/":
        return "inicio_sesion"
    if ruta == "/api/auth/logout/":
        return "cierre_sesion"
    return ACCIONES_POR_METODO.get(metodo.upper(), "otro")


def motivo_rechazo(codigo_estado):
    if codigo_estado >= 500:
        return "error del servidor"
    return MOTIVOS.get(codigo_estado, f"código {codigo_estado}")


def descripcion_generica(metodo, ruta, codigo_estado):
    accion = accion_para(metodo, ruta)
    exito = codigo_estado < 400
    if accion == "inicio_sesion":
        return "Inició sesión" if exito else f"Intentó iniciar sesión ({motivo_rechazo(codigo_estado)})"
    if accion == "cierre_sesion":
        return "Cerró sesión"

    coincidencia = RUTA_API.match(ruta)
    if not coincidencia or accion == "otro":
        texto = f"Solicitud {metodo} a {ruta}"
        return texto if exito else f"{texto} ({motivo_rechazo(codigo_estado)})"

    recurso, pk, extra = coincidencia.group("recurso", "pk", "extra")
    lista, singular, indefinido = RECURSOS.get(recurso, (recurso, recurso, recurso))
    if extra == "pdf" and pk:
        objeto = f"el PDF del contrato #{pk}"
    elif pk:
        objeto = f"{singular} #{pk}"
    elif accion == "creacion":
        objeto = indefinido
    else:
        objeto = lista

    if exito:
        return f"{VERBOS[accion]} {objeto}"
    return f"Intentó {VERBOS_INTENTO[accion]} {objeto} ({motivo_rechazo(codigo_estado)})"


def describir(request, descripcion):
    """Registra una descripción legible de la acción para el registro de auditoría."""
    django_request = getattr(request, "_request", request)
    django_request.auditoria_descripcion = descripcion


def nombre_proveedor(proveedor):
    if proveedor.codigo and proveedor.nombre:
        return f"«{proveedor.nombre}» ({proveedor.codigo})"
    return f"«{proveedor.nombre or proveedor.codigo or f'#{proveedor.pk}'}»"


def nombre_contrato(contrato):
    nombre = f"«{contrato.contrato}»" if contrato.contrato else f"#{contrato.pk}"
    return f"{nombre} del proveedor {nombre_proveedor(contrato.proveedor)}"
