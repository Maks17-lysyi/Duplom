from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

# Якщо твоя модель Game лежить у додатку lobbies, цей рядок імпортувати не обов'язково,
# бо ми використаємо строкову вказівку 'lobbies.Game'


class GamerProfile(models.Model):
    class Role(models.TextChoices):
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
        "cs2": {"entry", "support", "igl", "awp", "lurk", "flex"},
        "valorant": {"duelist", "initiator", "controller", "sentinel", "flex"},
        "dota2": {"pos1", "pos2", "pos3", "pos4", "pos5"},
    }

    class ValorantRank(models.TextChoices):
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
        HERALD = "herald", "Herald"
        GUARDIAN = "guardian", "Guardian"
        CRUSADER = "crusader", "Crusader"
        ARCHON = "archon", "Archon"
        LEGEND = "legend", "Legend"
        ANCIENT = "ancient", "Ancient"
        DIVINE = "divine", "Divine"
        IMMORTAL = "immortal", "Immortal"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="gamer_profile"
    )

    friends = models.ManyToManyField("self", blank=True, symmetrical=True)

    steam_id = models.CharField(max_length=64, blank=True)
    discord_id = models.CharField(max_length=64, blank=True)
    bio = models.TextField(blank=True)
    reputation_score = models.IntegerField(default=0)

    # ❗ ГОЛОВНА ЗМІНА: Тепер це зв'язок з моделлю Game з додатка lobbies
    main_game = models.ForeignKey(
        "lobbies.Game", on_delete=models.SET_NULL, null=True, blank=True, related_name="gamers"
    )

    role = models.CharField(max_length=16, choices=Role.choices, blank=True)
    rank = models.CharField(max_length=64, blank=True)  # Kept for legacy if needed

    # Nationality
    country = models.CharField(max_length=64, blank=True)

    # ❗ CS2 Specific (ДОДАНО ВАЛІДАТОРИ ТА ПОЛЕ ELO) ❗
    cs2_faceit_lvl = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    cs2_faceit_elo = models.PositiveIntegerField(null=True, blank=True, verbose_name="Faceit ELO")
    cs2_premier_rating = models.PositiveIntegerField(null=True, blank=True)

    # Valorant Specific
    valorant_rank = models.CharField(max_length=16, choices=ValorantRank.choices, blank=True)

    # Dota 2 Specific
    dota2_rank = models.CharField(max_length=16, choices=Dota2Rank.choices, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.user.username} profile"

    # ❗ ОНОВЛЕНО: Розумний вивід рангу (Пофіксив логіку з ELO) ❗
    @property
    def display_rank(self) -> str:
        """Розумний вивід рангу залежно від вибраної гри"""
        if not self.main_game:
            return "Unranked"

        game_slug = self.main_game.slug.lower()

        if game_slug == "cs2":
            parts = []
            if self.cs2_faceit_lvl:
                faceit_str = f"Faceit Lvl {self.cs2_faceit_lvl}"
                if self.cs2_faceit_elo:
                    faceit_str += f" ({self.cs2_faceit_elo} ELO)"
                parts.append(faceit_str)

            if self.cs2_premier_rating:
                parts.append(f"Premier {self.cs2_premier_rating}")

            return " | ".join(parts) if parts else "Unranked"

        elif game_slug == "valorant":
            if self.valorant_rank:
                return self.get_valorant_rank_display()
            return "Unranked"

        elif game_slug == "dota2":
            if self.dota2_rank:
                return self.get_dota2_rank_display()
            return "Unranked"

        # Якщо гра якась інша, виводимо стандартне поле
        return self.rank if self.rank else "Unranked"

    @property
    def reputation_badge(self) -> str:
        score = self.reputation_score or 0
        if score >= 100:
            return "Sheriff"
        if score >= 25:
            return "Trusted"
        return "Newbie"

    @classmethod
    def role_choices_for_game(cls, game: str):
        allowed = cls.ROLE_VALUES_BY_GAME.get(game)
        if not allowed:
            return cls.Role.choices
        return [(v, label) for (v, label) in cls.Role.choices if v in allowed]


# Запити в друзі
class FriendRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Очікує"
        ACCEPTED = "accepted", "Прийнято"
        REJECTED = "rejected", "Відхилено"

    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="sent_friend_requests", on_delete=models.CASCADE
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="received_friend_requests", on_delete=models.CASCADE
    )

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("from_user", "to_user")
        ordering = ["-created_at"]
        verbose_name = "Запит у друзі"
        verbose_name_plural = "Запити у друзі"

    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username} ({self.get_status_display()})"


@receiver(post_save, sender=get_user_model())
def create_gamer_profile(sender, instance, created, **kwargs):
    if created:
        GamerProfile.objects.create(user=instance)


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        FRIEND_REQUEST = "friend_request", "Запит у друзі"
        LOBBY_INVITE = "lobby_invite", "Запрошення в лобі"
        SYSTEM = "system", "Системне повідомлення"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_notifications",
    )
    notification_type = models.CharField(
        max_length=20, choices=NotificationType.choices, default=NotificationType.SYSTEM
    )
    lobby_id = models.IntegerField(null=True, blank=True)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"To {self.recipient.username}: {self.message}"



class DirectMessage(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="sent_messages", on_delete=models.CASCADE
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="received_messages", on_delete=models.CASCADE
    )
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]  # Сортуємо від найстаріших до найновіших

    def __str__(self):
        return f"From {self.sender.username} to {self.receiver.username}"
