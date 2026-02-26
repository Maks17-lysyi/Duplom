from django import forms

from .models import Lobby


class LobbyForm(forms.ModelForm):
    class Meta:
        model = Lobby
        fields = (
            "title",
            "game",
            "country",
            "required_rank",
            "required_role",
            "req_cs2_faceit_lvl",
            "req_cs2_premier_rating",
            "req_valorant_rank",
            "req_dota2_rank",
            "mic_required",
            "slots_total",
            "description",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4, "class": "squadup-input-neon"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit required_role choices by selected game (server-side), still complemented by JS.
        game = None
        if self.is_bound:
            game = self.data.get("game") or None
        elif getattr(self.instance, "game", None):
            game = self.instance.game

        if "required_role" in self.fields and game:
            allowed = Lobby.required_role_choices_for_game(game)
            # keep "Any" always
            self.fields["required_role"].choices = [("any", "Any")] + list(allowed)

        for name, field in self.fields.items():
            if name == "description":
                continue
            if name in {"game", "country", "required_rank", "required_role", "req_valorant_rank", "req_dota2_rank"}:
                field.widget.attrs.setdefault("class", "squadup-select-neon")
            elif name == "mic_required":
                field.widget.attrs.setdefault("class", "form-check-input squadup-check")
            else:
                field.widget.attrs.setdefault("class", "squadup-input-neon")

    def clean_required_role(self):
        role = self.cleaned_data.get("required_role") or "any"
        if role == "any":
            return "any"
        game = self.cleaned_data.get("game")
        allowed_values = {v for v, _ in Lobby.required_role_choices_for_game(game)}
        if role not in allowed_values:
            raise forms.ValidationError("Required role must match the selected game.")
        return role
