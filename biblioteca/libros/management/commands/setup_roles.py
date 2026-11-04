from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


ROLES = {
    "Lector": [
        ("libros", "view_libro"),
        ("libros", "view_prestamo"),
    ],
    "Bibliotecario": [
        ("libros", "view_libro"),
        ("libros", "add_libro"),
        ("libros", "change_libro"),
        ("libros", "delete_libro"),
        ("libros", "view_prestamo"),
        ("libros", "add_prestamo"),
        ("libros", "change_prestamo"),
        ("libros", "delete_prestamo"),
    ],
    "Administrador": [
        ("libros", "view_libro"),
        ("libros", "add_libro"),
        ("libros", "change_libro"),
        ("libros", "delete_libro"),
        ("libros", "view_prestamo"),
        ("libros", "add_prestamo"),
        ("libros", "change_prestamo"),
        ("libros", "delete_prestamo"),
        ("auth", "view_user"),
        ("auth", "add_user"),
        ("auth", "change_user"),
        ("auth", "delete_user"),
        ("auth", "view_group"),
        ("auth", "add_group"),
        ("auth", "change_group"),
        ("auth", "delete_group"),
    ],
}


class Command(BaseCommand):
    help = "Crea los grupos y permisos de la biblioteca."

    def handle(self, *args, **options):
        for nombre, permisos in ROLES.items():
            grupo, _ = Group.objects.get_or_create(name=nombre)
            permisos_grupo = [
                Permission.objects.get(
                    content_type__app_label=app,
                    codename=codename,
                )
                for app, codename in permisos
            ]
            grupo.permissions.set(permisos_grupo)
            self.stdout.write(f"Rol configurado: {nombre}")
