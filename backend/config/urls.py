from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from proveedores.views import ProveedorViewSet
from proveedores.auth_views import auth_state, csrf_cookie, login_view, logout_view

router = DefaultRouter()
router.register("proveedores", ProveedorViewSet, basename="proveedor")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/csrf/", csrf_cookie, name="auth-csrf"),
    path("api/auth/session/", auth_state, name="auth-session"),
    path("api/auth/login/", login_view, name="auth-login"),
    path("api/auth/logout/", logout_view, name="auth-logout"),
    path("api/", include(router.urls)),
]
