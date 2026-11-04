from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import LoginForm

app_name = "libros"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("registro/", views.registrar_usuario, name="registro"),
    path("login/",auth_views.LoginView.as_view(authentication_form=LoginForm,template_name="libros/login.html",next_page="libros:inicio",),name="login",),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("libros/<int:libro_id>/", views.detalle, name="detalle"),
    path("libros/<int:libro_id>/prestamo/",views.registrar_prestamo,name="registrar_prestamo",),
    path(
        "prestamos/vencidos/",
        views.prestamos_vencidos,
        name="prestamos_vencidos",
    ),
    path(
        "prestamos/<int:prestamo_id>/devolver/",
        views.registrar_devolucion,
        name="registrar_devolucion",
    ),
    path("crear/", views.crear_libro, name="crear_libro"),
    path("libros/<int:libro_id>/editar/", views.editar_libro,name="editar_libro",),
    path("libros/<int:libro_id>/eliminar/",views.eliminar_libro,name="eliminar_libro",),
]
