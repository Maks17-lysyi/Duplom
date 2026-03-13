from django.contrib import admin
from .models import Game, Lobby, Tournament # Переконайтеся, що всі ваші моделі імпортовані

# Якщо ви ще не реєстрували Game, додайте це:
@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'order')
    search_fields = ('name',)

# Реєстрація Турнірів для Адміністратора
@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ('title', 'game', 'date_time', 'prize', 'is_active')
    list_filter = ('game', 'is_active', 'date_time')
    search_fields = ('title', 'details')
    # Це дозволить адміну зручно заповнювати всі поля з вашої діаграми