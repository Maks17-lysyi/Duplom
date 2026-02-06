from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver


class Lobby(models.Model):
    class Game(models.TextChoices):
        CS2 = "cs2", "Counter-Strike 2"
        DOTA2 = "dota2", "Dota 2"
        VALORANT = "valorant", "Valorant"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        FULL = "full", "Full"
        ENDED = "ended", "Ended"

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

    ROLE_VALUES_BY_GAME = {
        Game.CS2: {"entry", "support", "igl", "awp", "lurk", "flex"},
        Game.VALORANT: {"duelist", "initiator", "controller", "sentinel", "flex"},
        Game.DOTA2: {"pos1", "pos2", "pos3", "pos4", "pos5"},
    }

    host = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="hosted_lobbies"
    )
    title = models.CharField(max_length=120)
    game = models.CharField(max_length=16, choices=Game.choices, default=Game.CS2)
    required_rank = models.CharField(
        max_length=16, choices=RequiredRank.choices, default=RequiredRank.ANY
    )
    required_role = models.CharField(
        max_length=16, choices=RequiredRole.choices, default=RequiredRole.ANY
    )
    mic_required = models.BooleanField(default=False)
    slots_total = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(2), MaxValueValidator(10)], default=5
    )
    slots_filled = models.PositiveSmallIntegerField(default=0, editable=False)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["host"],
                condition=Q(status="active"),
                name="uniq_active_lobby_per_host",
            )
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.title} ({self.get_game_display()})"

    @property
    def is_full(self) -> bool:
        return self.slots_filled >= self.slots_total

    def recalc_slots(self, *, save: bool = True) -> None:
        """
        Keep slots_filled in sync with LobbyParticipant count.
        Also auto-switch ACTIVE/FULL (but never un-end an ENDED lobby).
        """
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
    lobby = models.ForeignKey(
        Lobby, on_delete=models.CASCADE, related_name="participants"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lobby_participations",
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["lobby", "user"], name="uniq_lobby_participant"
            )
        ]
        ordering = ["joined_at"]

    def __str__(self) -> str:
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

