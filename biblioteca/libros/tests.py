from datetime import date, timedelta

from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.utils import timezone
from .models import Libro, Prestamo


class ImagenLibroTests(TestCase):
    def setUp(self):
        usuario = get_user_model().objects.create_superuser(
            username="admin",
            password="test-password-123",
        )
        self.client.force_login(usuario)
        self.libro = Libro.objects.create(
            titulo="Cien años de soledad",
            autor="Gabriel García Márquez",
            año=1967,
        )

    def test_crear_libro_guarda_url_de_portada(self):
        response = self.client.post(
            reverse("libros:crear_libro"),
            {
                "titulo": "El otoño del patriarca",
                "autor": "Gabriel García Márquez",
                "año": 1975,
                "imagen_url": "https://example.com/portada.jpg",
                "disponible": "on",
            },
        )

        self.assertRedirects(response, reverse("libros:inicio"))
        self.assertEqual(
            Libro.objects.get(titulo="El otoño del patriarca").imagen_url,
            "https://example.com/portada.jpg",
        )

    def test_editar_libro_actualiza_url_de_portada(self):
        response = self.client.post(
            reverse("libros:editar_libro", args=[self.libro.id]),
            {
                "titulo": self.libro.titulo,
                "autor": self.libro.autor,
                "año": self.libro.año,
                "imagen_url": "https://example.com/nueva-portada.jpg",
                "disponible": "on",
            },
        )

        self.assertRedirects(
            response,
            reverse("libros:detalle", args=[self.libro.id]),
        )
        self.libro.refresh_from_db()
        self.assertEqual(
            self.libro.imagen_url,
            "https://example.com/nueva-portada.jpg",
        )

    def test_rechaza_url_de_portada_invalida(self):
        response = self.client.post(
            reverse("libros:crear_libro"),
            {
                "titulo": "Libro de prueba",
                "autor": "Autor",
                "año": 2024,
                "imagen_url": "no-es-una-url",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ingrese una URL válida.")
        self.assertEqual(Libro.objects.count(), 1)

    @override_settings(BIBLIOTECA_ESCUDO_URL="https://example.com/escudo.png")
    def test_portada_y_escudo_se_muestran_en_lista(self):
        self.libro.imagen_url = "https://example.com/portada.jpg"
        self.libro.save()

        response = self.client.get(reverse("libros:inicio"))

        self.assertContains(response, 'src="https://example.com/escudo.png"')
        self.assertContains(response, 'src="https://example.com/portada.jpg"')

    def test_catalogo_redirige_a_login_si_no_hay_sesion(self):
        self.client.logout()

        response = self.client.get(reverse("libros:inicio"))

        self.assertRedirects(
            response,
            f"{reverse('libros:login')}?next={reverse('libros:inicio')}",
        )
        response = self.client.get(
            reverse("libros:detalle", args=[self.libro.pk])
        )
        self.assertRedirects(
            response,
            f"{reverse('libros:login')}?next="
            f"{reverse('libros:detalle', args=[self.libro.pk])}",
        )

    def test_login_abre_catalogo_y_detalle_usa_ruta_dinamica(self):
        self.client.logout()
        login_page = self.client.get(reverse("libros:login"))
        self.assertContains(login_page, "Regístrate")

        response = self.client.post(
            reverse("libros:login"),
            {"username": "admin", "password": "test-password-123"},
        )

        self.assertRedirects(response, reverse("libros:inicio"))
        response = self.client.get(reverse("libros:inicio"))
        self.assertContains(
            response,
            f'href="{reverse("libros:detalle", args=[self.libro.pk])}"',
        )
        self.assertEqual(
            reverse("libros:detalle", args=[self.libro.pk]),
            f"/libros/{self.libro.pk}/",
        )
        self.assertEqual(
            self.client.get(
                reverse("libros:detalle", args=[self.libro.pk])
            ).status_code,
            200,
        )

    def test_registro_crea_lector_y_permite_ir_al_login(self):
        self.client.logout()

        registration_page = self.client.get(reverse("libros:registro"))
        self.assertContains(registration_page, "cuenta de lector")
        self.assertNotContains(registration_page, "name=\"rol\"")
        self.assertContains(
            registration_page,
            reverse("libros:login"),
        )

        response = self.client.post(
            reverse("libros:registro"),
            {
                "username": "nuevolector",
                "password1": "Una-clave-segura-123",
                "password2": "Una-clave-segura-123",
                "rol": "Administrador",
            },
        )

        self.assertRedirects(
            response,
            reverse("libros:registro"),
            fetch_redirect_response=False,
        )
        response = self.client.get(reverse("libros:registro"))
        self.assertContains(
            response,
            "Registro completado. Ahora inicia sesión con tu cuenta.",
        )
        self.assertContains(response, reverse("libros:login"))
        self.assertNotIn("_auth_user_id", self.client.session)
        usuario = get_user_model().objects.get(username="nuevolector")
        self.assertTrue(usuario.check_password("Una-clave-segura-123"))
        self.assertEqual(
            list(usuario.groups.values_list("name", flat=True)),
            ["Lector"],
        )

    def test_lector_puede_consultar_catalogo_y_detalle_sin_editar(self):
        call_command("setup_roles", verbosity=0)
        lector = get_user_model().objects.create_user(
            username="lector",
            password="Clave-segura-123",
        )
        lector.groups.add(Group.objects.get(name="Lector"))
        Prestamo.objects.create(
            libro=self.libro,
            usuario=lector,
            persona=lector.username,
            fecha=date(2026, 11, 4),
        )
        self.client.force_login(lector)

        catalogo = self.client.get(reverse("libros:inicio"))
        detalle_url = reverse("libros:detalle", args=[self.libro.pk])
        self.assertContains(catalogo, detalle_url)

        detalle = self.client.get(detalle_url)
        self.assertContains(detalle, self.libro.titulo)
        self.assertContains(detalle, "Historial de préstamos")
        self.assertContains(detalle, lector.username)
        self.assertContains(detalle, "04/11/2026")
        self.assertNotContains(detalle, "Registrar Nuevo Préstamo")
        self.assertNotContains(detalle, "Editar este libro")
        self.assertEqual(
            self.client.get(reverse("libros:crear_libro")).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(reverse("libros:prestamos_vencidos")).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(
                reverse(
                    "libros:registrar_devolucion",
                    args=[self.libro.prestamo_set.get().pk],
                )
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(
                reverse("admin:auth_group_changelist")
            ).status_code,
            302,
        )

    def test_bibliotecario_puede_crear_libro_y_registrar_prestamo(self):
        call_command("setup_roles", verbosity=0)
        bibliotecario = get_user_model().objects.create_user(
            username="bibliotecario",
            password="Clave-segura-123",
        )
        bibliotecario.groups.add(Group.objects.get(name="Bibliotecario"))
        lector = get_user_model().objects.create_user(
            username="lector",
            password="Clave-segura-123",
        )
        lector.groups.add(Group.objects.get(name="Lector"))
        self.client.force_login(bibliotecario)

        create_response = self.client.post(
            reverse("libros:crear_libro"),
            {
                "titulo": "Libro del bibliotecario",
                "autor": "Autor",
                "año": 2024,
                "disponible": "on",
            },
        )
        self.assertRedirects(create_response, reverse("libros:inicio"))
        nuevo_libro = Libro.objects.get(titulo="Libro del bibliotecario")

        loan_response = self.client.post(
            reverse("libros:registrar_prestamo", args=[nuevo_libro.pk]),
            {
                "usuario": lector.pk,
                "fecha": "2026-11-04",
                "fecha_devolucion_prevista": "2026-11-18",
            },
        )
        self.assertRedirects(
            loan_response,
            reverse("libros:detalle", args=[nuevo_libro.pk]),
        )
        nuevo_libro.refresh_from_db()
        self.assertFalse(nuevo_libro.disponible)
        self.assertEqual(
            nuevo_libro.prestamo_set.get().usuario_id,
            lector.pk,
        )
        prestamo = nuevo_libro.prestamo_set.get()
        self.assertEqual(
            prestamo.fecha_devolucion_prevista,
            date(2026, 11, 18),
        )
        self.assertEqual(prestamo.estado, Prestamo.Estado.ACTIVO)
        self.assertIsNone(prestamo.fecha_devolucion)

    def test_prestamo_rechaza_fecha_prevista_anterior_a_la_fecha_de_prestamo(self):
        call_command("setup_roles", verbosity=0)
        lector = get_user_model().objects.create_user(
            username="lector_fecha",
            password="Clave-segura-123",
        )
        lector.groups.add(Group.objects.get(name="Lector"))
        self.client.force_login(
            get_user_model().objects.get(username="admin")
        )
        fecha_prestamo = timezone.localdate()

        missing_due_date_response = self.client.post(
            reverse("libros:registrar_prestamo", args=[self.libro.pk]),
            {
                "usuario": lector.pk,
                "fecha": fecha_prestamo.isoformat(),
            },
        )
        self.assertEqual(missing_due_date_response.status_code, 200)
        self.assertContains(
            missing_due_date_response,
            "Fecha prevista de devolución",
        )
        self.assertFalse(Prestamo.objects.exists())

        response = self.client.post(
            reverse("libros:registrar_prestamo", args=[self.libro.pk]),
            {
                "usuario": lector.pk,
                "fecha": fecha_prestamo.isoformat(),
                "fecha_devolucion_prevista": (
                    fecha_prestamo - timedelta(days=1)
                ).isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "La devolución prevista no puede ser anterior al préstamo.",
        )
        self.assertFalse(Prestamo.objects.exists())
        self.libro.refresh_from_db()
        self.assertTrue(self.libro.disponible)

    def test_devolucion_cierra_prestamo_y_reactiva_libro(self):
        self.libro.disponible = False
        self.libro.save(update_fields=("disponible",))
        prestamo = Prestamo.objects.create(
            libro=self.libro,
            persona="lector",
            fecha=timezone.localdate() - timedelta(days=3),
            fecha_devolucion_prevista=timezone.localdate() - timedelta(days=1),
        )

        response = self.client.post(
            reverse("libros:registrar_devolucion", args=[prestamo.pk])
        )

        self.assertRedirects(
            response,
            reverse("libros:detalle", args=[self.libro.pk]),
        )
        prestamo.refresh_from_db()
        self.libro.refresh_from_db()
        self.assertEqual(prestamo.estado, Prestamo.Estado.DEVUELTO)
        self.assertEqual(prestamo.fecha_devolucion, timezone.localdate())
        self.assertTrue(self.libro.disponible)

        duplicate_response = self.client.post(
            reverse("libros:registrar_devolucion", args=[prestamo.pk]),
            follow=False,
        )
        self.assertRedirects(
            duplicate_response,
            reverse("libros:detalle", args=[self.libro.pk]),
            fetch_redirect_response=False,
        )
        duplicate_detail = self.client.get(
            reverse("libros:detalle", args=[self.libro.pk])
        )
        self.assertContains(duplicate_detail, "Este préstamo ya fue devuelto.")
        prestamo.refresh_from_db()
        self.assertEqual(prestamo.fecha_devolucion, timezone.localdate())

        get_response = self.client.get(
            reverse("libros:registrar_devolucion", args=[prestamo.pk])
        )
        self.assertEqual(get_response.status_code, 405)

    def test_lista_de_vencidos_solo_incluye_prestamos_activos(self):
        call_command("setup_roles", verbosity=0)
        bibliotecario = get_user_model().objects.create_user(
            username="bibliotecario_vencidos",
            password="Clave-segura-123",
        )
        bibliotecario.groups.add(Group.objects.get(name="Bibliotecario"))
        fecha_vencimiento = timezone.localdate() - timedelta(days=1)
        vencido = Prestamo.objects.create(
            libro=self.libro,
            persona="lector vencido",
            fecha=fecha_vencimiento - timedelta(days=7),
            fecha_devolucion_prevista=fecha_vencimiento,
        )
        Prestamo.objects.create(
            libro=self.libro,
            persona="lector devuelto",
            fecha=fecha_vencimiento - timedelta(days=7),
            fecha_devolucion_prevista=fecha_vencimiento,
            fecha_devolucion=timezone.localdate(),
            estado=Prestamo.Estado.DEVUELTO,
        )
        self.client.force_login(bibliotecario)

        response = self.client.get(reverse("libros:prestamos_vencidos"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "lector vencido")
        self.assertNotContains(response, "lector devuelto")
        self.assertContains(
            response,
            reverse("libros:registrar_devolucion", args=[vencido.pk]),
        )
        self.assertContains(
            self.client.get(reverse("libros:inicio")),
            "Préstamos vencidos (1)",
        )

    def test_administrador_con_acceso_staff_puede_gestionar_usuarios(self):
        call_command("setup_roles", verbosity=0)
        administrador = get_user_model().objects.create_user(
            username="administrador",
            password="Clave-segura-123",
            is_staff=True,
        )
        administrador.groups.add(Group.objects.get(name="Administrador"))
        self.client.force_login(administrador)

        response = self.client.get(reverse("admin:auth_user_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.client.get(reverse("admin:auth_group_changelist")).status_code,
            200,
        )
        self.assertContains(
            self.client.get(reverse("libros:inicio")),
            reverse("admin:index"),
        )

    def test_usuario_sin_permiso_no_puede_consultar_catalogo(self):
        response = self.client.post(
            reverse("libros:registro"),
            {
                "username": "usuario_invalido",
                "password1": "Una-clave-segura-123",
                "password2": "Una-clave-segura-123",
            },
        )

        self.assertEqual(response.status_code, 302)
        usuario = get_user_model().objects.get(username="usuario_invalido")
        grupo = usuario.groups.get()
        grupo.permissions.clear()
        self.client.force_login(usuario)

        self.assertEqual(
            self.client.get(reverse("libros:inicio")).status_code,
            403,
        )
