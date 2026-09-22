from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import User

_ENTRADA = {"class": "campo__entrada"}

class LoginForm(AuthenticationForm):
    username = forms.EmailField(label="E-mail")
        
class CadastroForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email", "first_name")
        widgets = {
            "email": forms.EmailInput(attrs={**_ENTRADA, "placeholder": "voce@exemplo.com", "autofocus": True}),
            "first_name": forms.TextInput(attrs={**_ENTRADA, "placeholder": "Como podemos te chamar"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs.update(_ENTRADA)
        self.fields["password2"].widget.attrs.update(_ENTRADA)
        self.fields["first_name"].required = False
        
