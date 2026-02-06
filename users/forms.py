from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import GamerProfile

User = get_user_model()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in {"password1", "password2", "username", "email"}:
                field.widget.attrs.setdefault("class", "form-control squadup-input")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get("email", "")
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("email",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control squadup-input")


class GamerProfileForm(forms.ModelForm):
    class Meta:
        model = GamerProfile
        fields = ("steam_id", "discord_id", "bio", "main_game", "role", "rank")
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4, "class": "form-control squadup-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit role choices by selected game (server-side), still complemented by JS.
        game = None
        if self.is_bound:
            game = self.data.get("main_game") or None
        elif getattr(self.instance, "main_game", None):
            game = self.instance.main_game

        if "role" in self.fields and game:
            allowed = GamerProfile.role_choices_for_game(game)
            self.fields["role"].choices = [("", "—")] + list(allowed)

        for name, field in self.fields.items():
            if name == "bio":
                continue
            css = (
                "form-select squadup-input"
                if name in {"main_game", "role"}
                else "form-control squadup-input"
            )
            field.widget.attrs.setdefault("class", css)

    def clean_role(self):
        role = self.cleaned_data.get("role") or ""
        game = self.cleaned_data.get("main_game")
        if not role:
            return ""
        allowed_values = {v for v, _ in GamerProfile.role_choices_for_game(game)}
        if role not in allowed_values:
            raise forms.ValidationError("Role must match the selected game.")
        return role
