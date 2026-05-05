from django.contrib import admin

from .models import (
    Game,
    Lobby,
    Tournament,
    Team,
    GameServer,
    Match,
)

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "order")
    search_fields = ("name",)

@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ("title", "game", "date_time", "status", "max_teams") 
    list_filter = ("game", "status", "date_time")
    search_fields = ("title",)

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "captain", "created_at")

@admin.register(GameServer)
class GameServerAdmin(admin.ModelAdmin):
    list_display = ("ip_address", "is_busy")

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("tournament", "round_number", "team1", "team2", "status")
    list_filter = ("status", "tournament")