from django.db import models

class Libro(models.Model):
    titulo = models.CharField(max_length=200)
    autor= models.CharField(max_length=100)
    año = models.IntegerField()
    imagen_url = models.URLField(max_length=500, blank=True, default="")
    disponible = models.BooleanField(default=True)

    def __str__(self):
        return self.titulo

class Prestamo(models.Model):
    libro = models.ForeignKey(
        Libro,
        on_delete=models.CASCADE
    )
    persona= models.CharField(max_length=100)
    fecha= models.DateField()

    def __str__(self):
        return f"{self.libro} - {self.persona}"
