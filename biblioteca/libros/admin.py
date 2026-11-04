from django.contrib import admin
from .models import Libro, Prestamo


@admin.register(Libro)
class LibroAdmin(admin.ModelAdmin):
    list_display = ("titulo", "autor", "año", "disponible")
    list_filter = ("disponible",)
    search_fields = ("titulo", "autor")


@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    list_display = (
        "libro",
        "persona",
        "fecha",
        "fecha_devolucion_prevista",
        "fecha_devolucion",
        "estado",
    )
    list_filter = ("estado",)
    search_fields = ("libro__titulo", "persona", "usuario__username")
