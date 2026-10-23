import json
from json import JSONDecodeError

from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST


def _user_data(user):
    permisos = sorted(
        permiso.split(".", 1)[1]
        for permiso in user.get_all_permissions()
        if permiso.startswith("proveedores.")
    )
    return {
        "id": user.pk,
        "username": user.get_username(),
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_superuser": user.is_superuser,
        "roles": list(user.groups.order_by("name").values_list("name", flat=True)),
        "permisos": permisos,
    }


@require_GET
@ensure_csrf_cookie
def csrf_cookie(request):
    return JsonResponse({"csrf_token": get_token(request)})


@require_GET
@ensure_csrf_cookie
def auth_state(request):
    if not request.user.is_authenticated:
        return JsonResponse({"authenticated": False})
    return JsonResponse({"authenticated": True, "user": _user_data(request.user)})


@require_POST
@csrf_protect
def login_view(request):
    try:
        data = json.loads(request.body)
    except (JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"detail": "El cuerpo de la solicitud no es JSON válido."}, status=400)

    if not isinstance(data, dict):
        return JsonResponse({"detail": "Se esperaba un objeto con usuario y contraseña."}, status=400)

    username = data.get("username")
    password = data.get("password")
    if not isinstance(username, str) or not isinstance(password, str) or not username or not password:
        return JsonResponse({"detail": "Ingresa tu usuario y contraseña."}, status=400)

    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse({"detail": "Usuario o contraseña incorrectos."}, status=400)
    if not user.is_active:
        return JsonResponse({"detail": "Esta cuenta está desactivada."}, status=403)

    login(request, user)
    return JsonResponse({"authenticated": True, "user": _user_data(user)})


@require_POST
@csrf_protect
def logout_view(request):
    logout(request)
    return JsonResponse({"authenticated": False})
