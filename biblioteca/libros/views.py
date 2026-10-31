from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from .models import Libro, Prestamo


def inicio(request):
    libros = Libro.objects.all()
    return render(
        request,
        "libros/index.html",
        {
            "libros": libros
        },
    )


def detalle(request, libro_id):
    libro = get_object_or_404(Libro, id=libro_id)
    return render(request,"libros/detalle.html",{"libro": libro})

def registrar_prestamo(request, libro_id):
    libro = get_object_or_404(Libro, pk=libro_id)
    try:
        persona_name = request.POST["persona"]
        fecha_prestamo = request.POST["fecha"]
        if not persona_name or not fecha_prestamo:
            raise KeyError("campos vacios")
    except (KeyError, ValueError):
        return render(
            request,
            "libros/detalle.html",
            {
                "libro": libro,
                "error_message": "Por favor, ingrese el nombre de la persona y la fecha de préstamo.",
            },
        )
    else: 
        Prestamo.objects.create(
            libro=libro, 
            persona=persona_name, 
            fecha=fecha_prestamo
        )
        
        libro.disponible = False
        libro.save()

        return HttpResponseRedirect(reverse("libros:detalle", args=(libro.id,)))

def crear_libro(request):
    if request.method == "POST":
        try:
            titulo = request.POST["titulo"]
            autor = request.POST["autor"]
            año = request.POST["año"]
            imagen_url = request.POST.get("imagen_url", "").strip()
            disponible = True if "disponible" in request.POST else False
            if not titulo or not autor or not año:
                raise KeyError("campos vacios")
            if imagen_url:
                URLValidator()(imagen_url)

            Libro.objects.create(
                titulo=titulo,
                autor=autor,
                año=año,
                imagen_url=imagen_url,
                disponible=disponible
            )
            return HttpResponseRedirect(reverse("libros:inicio"))
        except (KeyError, ValueError, ValidationError):
            return render(
                request,
                "libros/crear.html",
                {
                    "error_message": "Por favor, ingrese todos los campos correctamente.",
                    "imagen_url": request.POST.get("imagen_url", ""),
                },
            )
    return render(request, "libros/crear.html")

def editar_libro(request, libro_id):
    libro = get_object_or_404(Libro, pk=libro_id)
    if request.method == "POST":
        try:
            libro.titulo = request.POST["titulo"]
            libro.autor = request.POST["autor"]
            libro.año = request.POST["año"]
            libro.imagen_url = request.POST.get("imagen_url", "").strip()
            libro.disponible = True if "disponible" in request.POST else False
            if libro.imagen_url:
                URLValidator()(libro.imagen_url)
            libro.save()
            return HttpResponseRedirect(reverse("libros:detalle", args=(libro.id,)))
        except (KeyError, ValueError, ValidationError):
            return render(
                request,
                "libros/editar.html",
                {
                    "libro": libro,
                    "error_message": "Por favor, ingrese todos los campos correctamente.",
                    "imagen_url": request.POST.get("imagen_url", ""),
                },
            )

    return render(
        request,
        "libros/editar.html",
        {"libro": libro, "imagen_url": libro.imagen_url},
    )

def eliminar_libro(request, libro_id):
    libro = get_object_or_404(Libro, pk=libro_id)
    if request.method == "POST":
        libro.delete()
        return HttpResponseRedirect(reverse("libros:inicio"))
    return render(request, "libros/eliminar.html", {"libro": libro})