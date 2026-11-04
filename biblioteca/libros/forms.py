from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm

from .models import Libro, Prestamo


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "autofocus": True,
                "class": "w-full border border-gray-300 rounded-lg px-3 py-2",
                "placeholder": "Usuario",
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full border border-gray-300 rounded-lg px-3 py-2",
                "placeholder": "Contraseña",
            }
        )
    )


class RegistroLectorForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = (
                "w-full border border-gray-300 rounded-lg px-3 py-2"
            )


class LibroForm(forms.ModelForm):
    imagen_url = forms.URLField(
        required=False,
        error_messages={"invalid": "Ingrese una URL válida."},
    )

    class Meta:
        model = Libro
        fields = ("titulo", "autor", "año", "imagen_url", "disponible")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = (
                "border border-gray-300 rounded-lg px-3 py-2"
            )


class PrestamoForm(forms.ModelForm):
    fecha_devolucion_prevista = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Fecha prevista de devolución",
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
                "La devolución prevista no puede ser anterior al préstamo.",
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