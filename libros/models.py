from django.conf import settings
from django.db import models
from django.utils import timezone

class Libro(models.Model):
    titulo = models.CharField(max_length=200)
    autor= models.CharField(max_length=100)
    año = models.IntegerField()
    imagen_url = models.URLField(max_length=500, blank=True, default="")
    disponible = models.BooleanField(default=True)

    def __str__(self):
        return self.titulo

class Prestamo(models.Model):
    class Estado(models.TextChoices):
        ACTIVO = "activo", "Activo"
        DEVUELTO = "devuelto", "Devuelto"

    libro = models.ForeignKey(
        Libro,
        on_delete=models.CASCADE
    )
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    persona= models.CharField(max_length=100)
    fecha= models.DateField()
    fecha_devolucion_prevista = models.DateField(null=True, blank=True)
    fecha_devolucion = models.DateField(null=True, blank=True)
    estado = models.CharField(
        max_length=10,
        choices=Estado.choices,
        default=Estado.ACTIVO,
    )

    @property
    def vencido(self):
        return (
            self.estado == self.Estado.ACTIVO
            and self.fecha_devolucion_prevista is not None
            and self.fecha_devolucion_prevista < timezone.localdate()
        )

    def __str__(self):
        return f"{self.libro} - {self.persona}"
