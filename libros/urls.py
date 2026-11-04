from django.urls import path

from . import views

app_name = "libros"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("registro/", views.registrar_usuario, name="registro"),
    path("login/", views.InicioSesionView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
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
