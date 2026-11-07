from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm

from .models import Libro, Prestamo


class LoginForm(AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": (
            "El usuario o la contraseña no son correctos. "
            "Verifica los datos e inténtalo de nuevo."
        ),
        "inactive": "Esta cuenta está inactiva. Comunícate con el administrador.",
    }

    username = forms.CharField(
        label="Nombre de usuario",
        widget=forms.TextInput(
            attrs={
                "autofocus": True,
                "class": "w-full border border-gray-300 rounded-lg px-3 py-2",
                "placeholder": "Usuario",
            }
        )
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full border border-gray-300 rounded-lg px-3 py-2",
                "placeholder": "Contraseña",
            }
        )
    )


class RegistroUsuarioForm(UserCreationForm):
    error_messages = {
        **UserCreationForm.error_messages,
        "password_mismatch": "Las contraseñas no coinciden. Escríbelas de nuevo.",
    }

    username = forms.CharField(
        label="Nombre de usuario",
        max_length=150,
        help_text=(
            "Usa hasta 150 caracteres: letras, números y @/./+/-/_."
        ),
        error_messages={
            "required": "Escribe un nombre de usuario.",
            "max_length": "El nombre de usuario no puede superar 150 caracteres.",
            "unique": "Ese nombre de usuario ya está registrado.",
            "invalid": "Usa letras, números y @/./+/-/_ en el nombre de usuario.",
        },
    )
    password1 = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput,
        error_messages={"required": "Escribe una contraseña."},
    )
    password2 = forms.CharField(
        label="Confirma tu contraseña",
        strip=False,
        widget=forms.PasswordInput,
        error_messages={"required": "Confirma tu contraseña."},
    )
    rol = forms.ChoiceField(
        label="Perfil que necesitas",
        choices=[
            ("Lector", "Lector"),
            ("Bibliotecario", "Bibliotecario"),
        ],
        help_text="El perfil define las opciones que tendrás en la biblioteca.",
        error_messages={
            "required": "Selecciona el perfil que necesitas.",
            "invalid_choice": "Selecciona uno de los perfiles disponibles.",
        },
    )

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "rol")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = (
                "w-full border border-gray-300 rounded-lg px-3 py-2"
            )


class LibroForm(forms.ModelForm):
    año = forms.IntegerField(
        label="Año de publicación",
        min_value=1000,
        max_value=9999,
        widget=forms.NumberInput(
            attrs={
                "min": 1000,
                "max": 9999,
                "step": 1,
                "inputmode": "numeric",
            }
        ),
        error_messages={
            "required": "Escribe el año de publicación.",
            "invalid": "Escribe el año con números, por ejemplo 1967.",
            "min_value": "El año debe tener cuatro dígitos.",
            "max_value": "El año no puede superar cuatro dígitos.",
        },
    )
    imagen_url = forms.URLField(
        required=False,
        error_messages={
            "invalid": (
                "Escribe una dirección web válida, por ejemplo "
                "https://ejemplo.com/portada.jpg."
            ),
        },
    )

    class Meta:
        model = Libro
        fields = ("titulo", "autor", "año", "imagen_url", "disponible")
        labels = {
            "titulo": "Título",
            "autor": "Autor",
            "año": "Año de publicación",
            "imagen_url": "Enlace de la portada",
            "disponible": "Disponible",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field, forms.BooleanField):
                field.widget.attrs["class"] = (
                    "h-4 w-4 rounded border-gray-300 text-blue-700 "
                    "focus:ring-blue-600"
                )
            else:
                field.widget.attrs["class"] = (
                    "w-full border border-gray-300 rounded-lg px-3 py-2 "
                    "focus:border-blue-600 focus:outline-none "
                    "focus:ring-2 focus:ring-blue-100"
                )


class PrestamoForm(forms.ModelForm):
    fecha_devolucion_prevista = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Fecha prevista de devolución",
        error_messages={
            "required": "Selecciona la fecha prevista de devolución.",
            "invalid": "Escribe una fecha válida para la devolución.",
        },
    )

    class Meta:
        model = Prestamo
        fields = ("usuario", "fecha", "fecha_devolucion_prevista")
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}),
            "fecha_devolucion_prevista": forms.DateInput(
                attrs={"type": "date"}
            ),
        }
        labels = {
            "usuario": "Lector",
            "fecha": "Fecha del préstamo",
            "fecha_devolucion_prevista": "Fecha prevista de devolución",
        }
        error_messages = {
            "usuario": {
                "required": "Selecciona el lector que recibe el libro.",
                "invalid_choice": "Selecciona un lector válido.",
            },
            "fecha": {
                "required": "Selecciona la fecha del préstamo.",
                "invalid": "Escribe una fecha válida para el préstamo.",
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["usuario"].queryset = (
            get_user_model()
            .objects.filter(groups__name="Lector", is_active=True)
            .distinct()
        )
        self.fields["usuario"].widget.attrs["class"] = (
            "border border-gray-300 rounded-lg px-3 py-2"
        )
        self.fields["fecha"].widget.attrs["class"] = (
            "border border-gray-300 rounded-lg px-3 py-2"
        )
        self.fields["fecha_devolucion_prevista"].widget.attrs["class"] = (
            "border border-gray-300 rounded-lg px-3 py-2"
        )

    def clean(self):
        cleaned_data = super().clean()
        fecha_prestamo = cleaned_data.get("fecha")
        fecha_devolucion_prevista = cleaned_data.get(
            "fecha_devolucion_prevista"
        )
        if (
            fecha_prestamo
            and fecha_devolucion_prevista
            and fecha_devolucion_prevista < fecha_prestamo
        ):
            self.add_error(
                "fecha_devolucion_prevista",
                "La fecha prevista de devolución no puede ser anterior "
                "a la fecha del préstamo.",
            )
        return cleaned_data

    def save(self, commit=True):
        prestamo = super().save(commit=False)
        prestamo.persona = (
            prestamo.usuario.get_full_name()
            or prestamo.usuario.get_username()
        )
        if commit:
            prestamo.save()
        return prestamo