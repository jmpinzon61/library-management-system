from django.urls import path
from . import views

app_name = "libros"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("<int:libro_id>/", views.detalle, name="detalle"),
    path("<int:libro_id>/prestamo/",  views.registrar_prestamo, name="registrar_prestamo"),
    path("crear/", views.crear_libro, name="crear_libro"),
    path("<int:libro_id>/editar/", views.editar_libro, name="editar_libro"),
    path("<int:libro_id>/eliminar/", views.eliminar_libro, name="eliminar_libro")
]
