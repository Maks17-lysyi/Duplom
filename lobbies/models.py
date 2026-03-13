from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

class Game(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    cover_url = models.URLField(max_length=500, blank=True)
    icon_url = models.URLField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

class Lobby(models.Model):

    class ValorantRank(models.TextChoices):
        ANY = "any", "Any"
        IRON = "iron", "Iron"
        BRONZE = "bronze", "Bronze"
        SILVER = "silver", "Silver"
        GOLD = "gold", "Gold"
        PLATINUM = "platinum", "Platinum"
        DIAMOND = "diamond", "Diamond"
        ASCENDANT = "ascendant", "Ascendant"
        IMMORTAL = "immortal", "Immortal"
        RADIANT = "radiant", "Radiant"

    class Dota2Rank(models.TextChoices):
        ANY = "any", "Any"
        HERALD = "herald", "Herald"
        GUARDIAN = "guardian", "Guardian"
        CRUSADER = "crusader", "Crusader"
        ARCHON = "archon", "Archon"
        LEGEND = "legend", "Legend"
        ANCIENT = "ancient", "Ancient"
        DIVINE = "divine", "Divine"
        IMMORTAL = "immortal", "Immortal"

    class EafcMode(models.TextChoices):
        ANY = "any", "Any Mode"
        PRO_CLUBS = "pro_clubs", "Pro Clubs"
        COOP = "coop", "Co-op Seasons"

    class DbdRole(models.TextChoices):
        ANY = "any", "Any Role"
        SURVIVOR = "survivor", "Survivor"
        KILLER = "killer", "Killer (Custom Game)"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        FULL = "full", "Full"
        ENDED = "ended", "Ended"
    
    class PlayStyle(models.TextChoices):
        COMPETITIVE = "competitive", "Competitive / Ranked"
        FOR_FUN = "fun", "For Fun / Casual"

    class RequiredRank(models.TextChoices):
        ANY = "any", "Any"
        LOW = "low", "Low"
        MID = "mid", "Mid"
        HIGH = "high", "High"

    class RequiredRole(models.TextChoices):
        ANY = "any", "Any"
        ENTRY = "entry", "Entry"
        SUPPORT = "support", "Support"
        IGL = "igl", "IGL"
        AWP = "awp", "AWP / Sniper"
        LURK = "lurk", "Lurker"
        FLEX = "flex", "Flex"
        DUELIST = "duelist", "Duelist"
        INITIATOR = "initiator", "Initiator"
        CONTROLLER = "controller", "Controller"
        SENTINEL = "sentinel", "Sentinel"
        POS1 = "pos1", "Dota Pos 1 (Carry)"
        POS2 = "pos2", "Dota Pos 2 (Mid)"
        POS3 = "pos3", "Dota Pos 3 (Offlane)"
        POS4 = "pos4", "Dota Pos 4 (Soft Support)"
        POS5 = "pos5", "Dota Pos 5 (Hard Support)"
        STRIKER = "striker", "Striker / Forward"
        MIDFIELDER = "midfield", "Midfielder"
        DEFENDER = "defender", "Defender"
        GOALKEEPER = "gk", "Goalkeeper"
        LOOPER = "looper", "Looper / Distraction"
        GEN_RUSHER = "gen_rusher", "Objective / Gen Rusher"
        HEALER = "healer", "Altruistic / Healer"

    ROLE_VALUES_BY_GAME = {
        "cs2": {"entry", "support", "igl", "awp", "lurk", "flex"},
        "valorant": {"duelist", "initiator", "controller", "sentinel", "flex"},
        "dota2": {"pos1", "pos2", "pos3", "pos4", "pos5"},
        "eafc26": {"striker", "midfield", "defender", "gk", "flex"},
        "dbd": {"looper", "gen_rusher", "healer", "flex"},
    }

    host = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="hosted_lobbies")
    title = models.CharField(max_length=120)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="lobbies", null=True)
    play_style = models.CharField(max_length=16, choices=PlayStyle.choices, default=PlayStyle.COMPETITIVE)
    required_rank = models.CharField(max_length=16, choices=RequiredRank.choices, default=RequiredRank.ANY)
    required_role = models.CharField(max_length=16, choices=RequiredRole.choices, default=RequiredRole.ANY)
    country = models.CharField(max_length=64, blank=True)

    # CS2
    req_cs2_faceit_lvl_min = models.PositiveSmallIntegerField(null=True, blank=True)
    req_cs2_faceit_lvl_max = models.PositiveSmallIntegerField(null=True, blank=True)
    req_cs2_premier_rating_min = models.PositiveIntegerField(null=True, blank=True)
    req_cs2_premier_rating_max = models.PositiveIntegerField(null=True, blank=True)

    # Others
    req_valorant_rank = models.CharField(max_length=16, choices=ValorantRank.choices, default=ValorantRank.ANY)
    req_dota2_rank = models.CharField(max_length=16, choices=Dota2Rank.choices, default=Dota2Rank.ANY)
    req_eafc_mode = models.CharField(max_length=16, choices=EafcMode.choices, default=EafcMode.ANY)
    req_dbd_role = models.CharField(max_length=16, choices=DbdRole.choices, default=DbdRole.ANY)
    
    mic_required = models.BooleanField(default=False)
    slots_total = models.PositiveSmallIntegerField(validators=[MinValueValidator(2), MaxValueValidator(10)], default=5)
    slots_filled = models.PositiveSmallIntegerField(default=0, editable=False)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["host"], condition=Q(status="active"), name="uniq_active_lobby_per_host")
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.game.name if self.game else 'No Game'})"

    @property
    def is_full(self) -> bool:
        return self.slots_filled >= self.slots_total

    def recalc_slots(self, *, save: bool = True) -> None:
        count = self.participants.count()
        self.slots_filled = count
        if self.status != self.Status.ENDED:
            self.status = self.Status.FULL if count >= self.slots_total else self.Status.ACTIVE
        if save:
            self.save(update_fields=["slots_filled", "status"])

    @classmethod
    def required_role_choices_for_game(cls, game: str):
        allowed = cls.ROLE_VALUES_BY_GAME.get(game)
        if not allowed:
            return cls.RequiredRole.choices
        return [(v, label) for (v, label) in cls.RequiredRole.choices if v in allowed]


class LobbyParticipant(models.Model):
    lobby = models.ForeignKey(Lobby, on_delete=models.CASCADE, related_name="participants")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lobby_participations")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["lobby", "user"], name="uniq_lobby_participant")
        ]
        ordering = ["joined_at"]

    def __str__(self):
        return f"{self.user.username} in {self.lobby_id}"

@receiver(post_save, sender=Lobby)
def add_host_as_participant(sender, instance: Lobby, created: bool, **kwargs):
    if not created:
        return
    LobbyParticipant.objects.get_or_create(lobby=instance, user=instance.host)
    instance.recalc_slots()

@receiver(post_save, sender=LobbyParticipant)
def update_lobby_slots_on_join(sender, instance: LobbyParticipant, created: bool, **kwargs):
    if created:
        instance.lobby.recalc_slots()

@receiver(post_delete, sender=LobbyParticipant)
def update_lobby_slots_on_leave(sender, instance: LobbyParticipant, **kwargs):
    instance.lobby.recalc_slots()

class ChatMessage(models.Model):
    lobby = models.ForeignKey(Lobby, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender}: {self.content[:20]}"

class Tournament(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="tournaments", verbose_name="Гра")
    
    title = models.CharField(max_length=200, verbose_name="Заголовок турніру")
    
    # НОВЕ ПОЛЕ ДЛЯ ЗАВАНТАЖЕННЯ ФАЙЛІВ КАРТИНОК
    image = models.ImageField(upload_to='tournaments/covers/', blank=True, null=True, verbose_name="Зображення (Файл)")
    
    # Старе поле для силок залишаємо
    image_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="Зображення (URL)") 
    
    format_type = models.CharField(max_length=100, verbose_name="Формат турніру", help_text="Наприклад: 5v5, 1v1, Double Elimination")
    date_time = models.DateTimeField(verbose_name="Дата та час проведення")
    details = models.TextField(verbose_name="Деталі та формат")
    rules = models.TextField(verbose_name="Правила")
    prize = models.CharField(max_length=200, verbose_name="Приз")
    contacts = models.CharField(max_length=200, verbose_name="Контакти (Discord, Telegram тощо)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, verbose_name="Активний")

    class Meta:
        ordering = ['-date_time']
        verbose_name = "Турнір"
        verbose_name_plural = "Турніри"

    def __str__(self):
        return f"{self.title} ({self.game.name})"