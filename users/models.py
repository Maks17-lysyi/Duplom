from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class GamerProfile(models.Model):
    class MainGame(models.TextChoices):
        CS2 = "cs2", "Counter-Strike 2"
        DOTA2 = "dota2", "Dota 2"
        VALORANT = "valorant", "Valorant"

    class Role(models.TextChoices):
        # CS2-ish
        ENTRY = "entry", "Entry"
        SUPPORT = "support", "Support"
        IGL = "igl", "IGL"
        AWP = "awp", "AWP / Sniper"
        LURK = "lurk", "Lurker"
        FLEX = "flex", "Flex"
        # Valorant-ish
        DUELIST = "duelist", "Duelist"
        INITIATOR = "initiator", "Initiator"
        CONTROLLER = "controller", "Controller"
        SENTINEL = "sentinel", "Sentinel"
        # Dota positions
        POS1 = "pos1", "Dota Pos 1 (Carry)"
        POS2 = "pos2", "Dota Pos 2 (Mid)"
        POS3 = "pos3", "Dota Pos 3 (Offlane)"
        POS4 = "pos4", "Dota Pos 4 (Soft Support)"
        POS5 = "pos5", "Dota Pos 5 (Hard Support)"

    ROLE_VALUES_BY_GAME = {
        MainGame.CS2: {"entry", "support", "igl", "awp", "lurk", "flex"},
        MainGame.VALORANT: {"duelist", "initiator", "controller", "sentinel", "flex"},
        MainGame.DOTA2: {"pos1", "pos2", "pos3", "pos4", "pos5"},
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

    steam_id = models.CharField(max_length=64, blank=True)
    discord_id = models.CharField(max_length=64, blank=True)
    bio = models.TextField(blank=True)
    reputation_score = models.IntegerField(default=0)
    main_game = models.CharField(
        max_length=16, choices=MainGame.choices, default=MainGame.CS2
    )
    role = models.CharField(max_length=16, choices=Role.choices, blank=True)
    rank = models.CharField(max_length=64, blank=True) # Kept for legacy if needed

    # Nationality
    country = models.CharField(max_length=64, blank=True)

    # CS2 Specific
    cs2_faceit_lvl = models.PositiveSmallIntegerField(null=True, blank=True)
    cs2_premier_rating = models.PositiveIntegerField(null=True, blank=True)

    # Valorant Specific
    valorant_rank = models.CharField(max_length=16, choices=ValorantRank.choices, blank=True)

    # Dota 2 Specific
    dota2_rank = models.CharField(max_length=16, choices=Dota2Rank.choices, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.user.username} profile"

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


@receiver(post_save, sender=get_user_model())
def create_gamer_profile(sender, instance, created, **kwargs):
    if created:
        GamerProfile.objects.create(user=instance)
