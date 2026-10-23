from .auditoria import accion_para, descripcion_generica
from .models import RegistroAuditoria


class AuditoriaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        usuario_inicial = request.user if request.user.is_authenticated else None
        usuario_id = usuario_inicial.pk if usuario_inicial else None
        nombre_usuario = usuario_inicial.get_username() if usuario_inicial else ""
        ruta = request.path_info
        response = self.get_response(request)

        if ruta == "/api/auth/login/" and response.status_code < 400:
            usuario = request.user
            if usuario.is_authenticated:
                usuario_id = usuario.pk
                nombre_usuario = usuario.get_username()
        elif (
            not usuario_id
            or not ruta.startswith("/api/")
            or (ruta.startswith("/api/auditoria/") and response.status_code < 400)
            or ruta in ("/api/auth/csrf/", "/api/auth/session/")
        ):
            return response

        if nombre_usuario:
            descripcion = getattr(request, "auditoria_descripcion", None) or descripcion_generica(
                request.method, ruta, response.status_code
            )
            RegistroAuditoria.objects.create(
                usuario_id=usuario_id,
                nombre_usuario=nombre_usuario,
                accion=accion_para(request.method, ruta),
                descripcion=descripcion[:500],
                metodo=request.method,
                ruta=ruta[:255],
                codigo_estado=response.status_code,
                direccion_ip=request.META.get("REMOTE_ADDR"),
            )
        return response
