from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from .models import Libro


class ImagenLibroTests(TestCase):
    def setUp(self):
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
        self.assertContains(response, "ingrese todos los campos correctamente")
        self.assertEqual(Libro.objects.count(), 1)

    @override_settings(BIBLIOTECA_ESCUDO_URL="https://example.com/escudo.png")
    def test_portada_y_escudo_se_muestran_en_lista(self):
        self.libro.imagen_url = "https://example.com/portada.jpg"
        self.libro.save()

        response = self.client.get(reverse("libros:inicio"))

        self.assertContains(response, 'src="https://example.com/escudo.png"')
        self.assertContains(response, 'src="https://example.com/portada.jpg"')
