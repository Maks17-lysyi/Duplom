from django import forms
from .models import Lobby

COUNTRY_CHOICES = [
    ("", "Anywhere"),
    ("UA", "Ukraine"),
    ("PL", "Poland"),
    ("US", "USA"),
    ("UK", "United Kingdom"),
    ("DE", "Germany"),
    ("FR", "France"),
]

CS2_PLATFORM_CHOICES = [
    ("", "Select Platform"),
    ("faceit", "Faceit"),
    ("premier", "Premier"),
    ("fun", "For Fun (No requirements)"),
]

class LobbyForm(forms.ModelForm):
    country = forms.ChoiceField(choices=COUNTRY_CHOICES, required=False)
    cs2_platform_selector = forms.ChoiceField(choices=CS2_PLATFORM_CHOICES, required=False, label="Platform")

    class Meta:
        model = Lobby
        # Я забрав "required_rank" звідси, щоб форма не падала приховано!
        fields = (
            "title",
            "game",
            "play_style",
            "country",
            "required_role",
            "req_cs2_faceit_lvl_min",
            "req_cs2_faceit_lvl_max",
            "req_cs2_premier_rating_min",
            "req_cs2_premier_rating_max",
            "req_valorant_rank",
            "req_dota2_rank",
            "req_eafc_mode",
            "req_dbd_role",
            "mic_required",
            "slots_total",
            "description",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "req_cs2_faceit_lvl_min": forms.NumberInput(attrs={"placeholder": "Min (e.g. 3)"}),
            "req_cs2_faceit_lvl_max": forms.NumberInput(attrs={"placeholder": "Max (e.g. 7)"}),
            "req_cs2_premier_rating_min": forms.NumberInput(attrs={"placeholder": "Min (e.g. 10000)"}),
            "req_cs2_premier_rating_max": forms.NumberInput(attrs={"placeholder": "Max (e.g. 15000)"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        game = None
        if self.is_bound:
            game = self.data.get("game") or None
        elif getattr(self.instance, "game", None):
            game = self.instance.game

        if "required_role" in self.fields and game:
            allowed = Lobby.required_role_choices_for_game(game)
            self.fields["required_role"].choices = [("any", "Any")] + list(allowed)

        for name, field in self.fields.items():
            if name == "description":
                field.widget.attrs.setdefault("class", "squadup-input-neon w-100")
            elif name in {"game", "country", "play_style", "required_role", "req_valorant_rank", "req_dota2_rank", "req_eafc_mode", "req_dbd_role", "cs2_platform_selector"}:
                field.widget.attrs.setdefault("class", "squadup-select-neon w-100")
            elif name == "mic_required":
                field.widget.attrs.setdefault("class", "form-check-input toggle-input d-none")
            else:
                field.widget.attrs.setdefault("class", "squadup-input-neon w-100")

    def clean_required_role(self):
        role = self.cleaned_data.get("required_role") or "any"
        if role == "any":
            return "any"
            
        game = self.cleaned_data.get("game")
        if not game:
             return role
             
        allowed_values = {v for v, _ in Lobby.required_role_choices_for_game(game.slug)}
        
        if role not in allowed_values:
            raise forms.ValidationError("Вибрана роль не підходить для цієї гри.")
            
        return role

    def clean(self):
        cleaned_data = super().clean()
        
        f_min = cleaned_data.get("req_cs2_faceit_lvl_min")
        f_max = cleaned_data.get("req_cs2_faceit_lvl_max")
        if f_min and f_max and f_min > f_max:
            self.add_error("req_cs2_faceit_lvl_max", "Max level cannot be less than Min level.")

        p_min = cleaned_data.get("req_cs2_premier_rating_min")
        p_max = cleaned_data.get("req_cs2_premier_rating_max")
        if p_min and p_max and p_min > p_max:
            self.add_error("req_cs2_premier_rating_max", "Max rating cannot be less than Min rating.")

        return cleaned_data