from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from lobbies.models import Game
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
        fields = (
            "steam_id",
            "discord_id",
            "bio",
            "country",
            "main_game",
            "role",
            "rank",
            "cs2_faceit_lvl",
            "cs2_faceit_elo",  # ❗ ОСЬ ТУТ Я ДОДАВ НОВЕ ПОЛЕ ❗
            "cs2_premier_rating",
            "valorant_rank",
            "dota2_rank",
        )
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4, "class": "form-control squadup-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 1. Робимо список ігор динамічним (беремо з БД)
        if "main_game" in self.fields:
            self.fields["main_game"].queryset = Game.objects.filter(is_active=True).order_by(
                "order"
            )
            self.fields["main_game"].empty_label = "--- Any Game / Not set ---"

        # 2. Обмежуємо ролі залежно від вибраної гри
        game_slug = None
        if self.is_bound:
            # Якщо форму відправили, отримуємо ID гри і шукаємо її slug
            game_id = self.data.get("main_game")
            if game_id:
                try:
                    game_slug = Game.objects.get(id=game_id).slug
                except Game.DoesNotExist:
                    game_slug = None
        elif getattr(self.instance, "main_game", None):
            # Якщо форму просто відкрили для редагування, беремо slug зі збереженої гри
            game_slug = self.instance.main_game.slug

        if "role" in self.fields:
            if game_slug:
                allowed = GamerProfile.role_choices_for_game(game_slug)
                self.fields["role"].choices = [("", "—")] + list(allowed)
            else:
                # Якщо гру не вибрано, показуємо всі ролі
                self.fields["role"].choices = [("", "—")] + list(GamerProfile.Role.choices)

        # 3. Застосовуємо правильні CSS класи
        for name, field in self.fields.items():
            if name == "bio":
                continue
            if name in {"main_game", "role", "valorant_rank", "dota2_rank"}:
                css = "form-select squadup-input"
            else:
                css = "form-control squadup-input"
            field.widget.attrs.setdefault("class", css)

    def clean_role(self):
        role = self.cleaned_data.get("role") or ""
        game_obj = self.cleaned_data.get("main_game")  # Тепер це об'єкт моделі Game

        if not role:
            return ""

        # Отримуємо slug гри для перевірки ролей (або None, якщо гру не вибрано)
        game_slug = game_obj.slug if game_obj else None

        allowed_values = {v for v, _ in GamerProfile.role_choices_for_game(game_slug)}

        if role not in allowed_values:
            raise forms.ValidationError("Role must match the selected game.")
        return role
