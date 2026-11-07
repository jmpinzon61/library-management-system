import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import (
    login_required,
    permission_required,
)
from django.contrib.auth.models import Group
from django.contrib.auth.views import LoginView, LogoutView
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from .forms import (
    AsistenteBibliotecaForm,
    LibroForm,
    LoginForm,
    PrestamoForm,
    RegistroUsuarioForm,
)
from .models import Libro, Prestamo
from .services.node_service import (
    NodeServiceError,
    generate_book_summary,
    generate_recommendations,
    get_overdue_notifications,
    sync_overdue_notifications,
)

logger = logging.getLogger(__name__)


class InicioSesionView(LoginView):
    authentication_form = LoginForm
    template_name = "libros/login.html"

    def get_success_url(self):
        redirect_url = self.get_redirect_url()
        if redirect_url:
            return redirect_url
        if self.request.user.is_staff and self.request.user.has_perm(
            "auth.view_user"
        ):
            return reverse("admin:index")
        return reverse("libros:inicio")


@login_required
@permission_required("libros.view_libro", raise_exception=True)
def inicio(request):
    libros = Libro.objects.all()
    prestamos_vencidos = Prestamo.objects.filter(
        estado=Prestamo.Estado.ACTIVO,
        fecha_devolucion_prevista__lt=timezone.localdate(),
    )
    return render(
        request,
        "libros/index.html",
        {
            "libros": libros,
            "cantidad_prestamos_vencidos": (
                prestamos_vencidos.count()
                if request.user.has_perm("libros.change_prestamo")
                else 0
            ),
            "escudo_url": settings.BIBLIOTECA_ESCUDO_URL
            or "https://d3nmwx7scpuzgc.cloudfront.net/sites/default/files/media/image/blaa-rgb-blanco.png",
        },
    )


@login_required
@permission_required("libros.view_libro", raise_exception=True)
def detalle(request, libro_id):
    libro = get_object_or_404(Libro, pk=libro_id)
    return render(
        request,
        "libros/detalle.html",
        _detalle_context(request, libro),
    )


def _detalle_context(request, libro):
    prestamos = libro.prestamo_set.select_related("usuario").order_by(
        "-fecha"
    )
    form = None

    if libro.disponible and request.user.has_perms(
        ("libros.add_prestamo", "libros.change_libro")
    ):
        form = PrestamoForm(
            initial={"fecha": timezone.localdate()}
        )

    return {
        "libro": libro,
        "prestamo_form": form,
        "prestamos": prestamos,
    }


@login_required
@permission_required("libros.view_libro", raise_exception=True)
@require_POST
def resumen_ia(request, libro_id):
    libro = get_object_or_404(Libro, pk=libro_id)
    book = {
        "id": libro.id,
        "title": libro.titulo,
        "author": libro.autor,
        "year": libro.año,
    }
    try:
        summary = generate_book_summary(book)
    except NodeServiceError as error:
        logger.warning("No se pudo generar el resumen bibliográfico.", exc_info=True)
        messages.error(request, str(error))
        return redirect("libros:detalle", libro_id=libro.id)

    context = _detalle_context(request, libro)
    context["resumen_ia"] = summary
    return render(request, "libros/detalle.html", context)


@login_required
@permission_required("libros.view_libro", raise_exception=True)
@require_http_methods(["GET", "POST"])
def asistente_ia(request):
    form = AsistenteBibliotecaForm(
        request.POST if request.method == "POST" else None
    )
    answer = None

    if request.method == "POST" and form.is_valid():
        catalog = [
            {
                "id": libro.id,
                "title": libro.titulo,
                "author": libro.autor,
                "year": libro.año,
            }
            for libro in Libro.objects.filter(disponible=True).order_by("titulo")[:100]
        ]
        try:
            answer = generate_recommendations(
                form.cleaned_data["pregunta"],
                catalog,
            )
        except NodeServiceError as error:
            logger.warning("Falló la solicitud de recomendaciones con IA.", exc_info=True)
            messages.error(request, str(error))

    return render(
        request,
        "libros/asistente_ia.html",
        {"form": form, "respuesta_ia": answer},
    )


@require_http_methods(["GET", "POST"])
def registrar_usuario(request):
    form = RegistroUsuarioForm(
        request.POST if request.method == "POST" else None
    )
    registration_result = None

    if request.method == "POST" and form.is_valid():
        usuario = form.save()
        rol = form.cleaned_data["rol"]
        grupo, _ = Group.objects.get_or_create(name=rol)
        usuario.groups.add(grupo)
        request.session["registration_result"] = rol
        return redirect("libros:registro")

    if request.method == "GET":
        registration_result = request.session.pop(
            "registration_result",
            None,
        )

    return render(
        request,
        "libros/registro.html",
        {
            "form": form,
            "registration_result": registration_result,
        },
    )


@login_required
@permission_required("libros.add_libro", raise_exception=True)
@require_http_methods(["GET", "POST"])
def crear_libro(request):
    form = LibroForm(
        request.POST if request.method == "POST" else None
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("libros:inicio")

    return render(request, "libros/crear.html", {"form": form})


@login_required
@permission_required("libros.change_libro", raise_exception=True)
@require_http_methods(["GET", "POST"])
def editar_libro(request, libro_id):
    libro = get_object_or_404(Libro, pk=libro_id)
    form = LibroForm(
        request.POST if request.method == "POST" else None,
        instance=libro,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("libros:detalle", libro_id=libro.id)

    return render(
        request,
        "libros/editar.html",
        {"libro": libro, "form": form},
    )


@login_required
@permission_required("libros.delete_libro", raise_exception=True)
@require_http_methods(["GET", "POST"])
def eliminar_libro(request, libro_id):
    libro = get_object_or_404(Libro, pk=libro_id)

    if request.method == "POST":
        libro.delete()
        return redirect("libros:inicio")

    return render(request, "libros/eliminar.html", {"libro": libro})


@login_required
@permission_required(
    ("libros.add_prestamo", "libros.change_libro"),
    raise_exception=True,
)
@require_POST
def registrar_prestamo(request, libro_id):
    libro = get_object_or_404(Libro, pk=libro_id)
    form = PrestamoForm(request.POST)

    if form.is_valid():
        with transaction.atomic():
            libro = get_object_or_404(
                Libro.objects.select_for_update(),
                pk=libro_id,
            )
            if libro.disponible:
                prestamo = form.save(commit=False)
                prestamo.libro = libro
                # form.usuario es el lector que recibe el libro.
                prestamo.save()

                libro.disponible = False
                libro.save(update_fields=["disponible"])

                return redirect("libros:detalle", libro_id=libro.id)

            form.add_error(
                None,
                "Este libro no está disponible para préstamo.",
            )

    return render(
        request,
        "libros/detalle.html",
        {
            "libro": libro,
            "prestamo_form": form,
            "prestamos": libro.prestamo_set.select_related("usuario"),
        },
    )


@login_required
@permission_required(
    ("libros.view_prestamo", "libros.change_prestamo"),
    raise_exception=True,
)
def prestamos_vencidos(request):
    prestamos = (
        Prestamo.objects.filter(
            estado=Prestamo.Estado.ACTIVO,
            fecha_devolucion_prevista__lt=timezone.localdate(),
        )
        .select_related("libro", "usuario")
        .order_by("fecha_devolucion_prevista", "libro__titulo")
    )
    try:
        notificaciones = get_overdue_notifications()
    except NodeServiceError as error:
        logger.warning("No se pudo consultar el microservicio de alertas.", exc_info=True)
        notificaciones = []
        messages.error(request, str(error))

    return render(
        request,
        "libros/prestamos_vencidos.html",
        {"prestamos": prestamos, "notificaciones": notificaciones},
    )


@login_required
@permission_required(
    ("libros.view_prestamo", "libros.change_prestamo"),
    raise_exception=True,
)
@require_POST
def procesar_alertas_vencidas(request):
    prestamos = Prestamo.objects.filter(
        estado=Prestamo.Estado.ACTIVO,
        fecha_devolucion_prevista__lt=timezone.localdate(),
    ).select_related("libro", "usuario")
    loans = [
        {
            "loanId": prestamo.id,
            "bookTitle": prestamo.libro.titulo,
            "borrower": (
                prestamo.usuario.username
                if prestamo.usuario_id
                else prestamo.persona.strip()
            )
            or "Lector sin identificar",
            "dueDate": prestamo.fecha_devolucion_prevista.isoformat(),
        }
        for prestamo in prestamos
    ]

    try:
        result = sync_overdue_notifications(loans)
        messages.success(
            request,
            f"Alertas sincronizadas: {result.get('synchronized', 0)} préstamo(s).",
        )
    except NodeServiceError as error:
        logger.warning("Falló la sincronización de alertas vencidas.", exc_info=True)
        messages.error(request, str(error))

    return redirect("libros:prestamos_vencidos")


@login_required
@permission_required("libros.change_prestamo", raise_exception=True)
@require_POST
def registrar_devolucion(request, prestamo_id):
    with transaction.atomic():
        prestamo = get_object_or_404(
            Prestamo.objects.select_for_update(),
            pk=prestamo_id,
        )
        if prestamo.estado == Prestamo.Estado.DEVUELTO:
            messages.warning(
                request,
                "Este préstamo ya fue devuelto.",
            )
        else:
            libro = get_object_or_404(
                Libro.objects.select_for_update(),
                pk=prestamo.libro_id,
            )
            prestamo.estado = Prestamo.Estado.DEVUELTO
            prestamo.fecha_devolucion = timezone.localdate()
            prestamo.save(
                update_fields=("estado", "fecha_devolucion")
            )
            libro.disponible = True
            libro.save(update_fields=("disponible",))
            messages.success(
                request,
                "La devolución se registró correctamente.",
            )

    return redirect(
        "libros:detalle",
        libro_id=prestamo.libro_id,
    )