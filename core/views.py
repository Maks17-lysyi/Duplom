import json

from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q  # <--- ВАЖЛИВО ДЛЯ ПОШУКУ! ДОДАЙ ЦЕЙ ІМПОРТ НА ПОЧАТОК ФАЙЛУ
from users.models import Notification
from lobbies.models import Lobby, Game, Tournament
from users.models import FriendRequest, GamerProfile  # Переконайтеся, що моделі друзів знаходяться в users.models

User = get_user_model()


def home(request):
    """
    Dashboard: list active lobbies + filters.
    """
    game_choices = Game.objects.filter(is_active=True).order_by('order')
    qs = (
        Lobby.objects.select_related("host")
        .prefetch_related("participants__user")
        .filter(status__in=[Lobby.Status.ACTIVE, Lobby.Status.FULL])
    )

    # --- НОВИЙ БЛОК ДЛЯ ПОШУКУ ПО НАЗВІ/ХОСТУ ---
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(title__icontains=q) | 
            Q(game__name__icontains=q) | 
            Q(host__username__icontains=q)
        )
    # ---------------------------------------------

    game = request.GET.get("game") or ""
    # Optional filtering parameters
    country = request.GET.get("country") or ""
    role = request.GET.get("role") or ""
    mic = request.GET.get("mic") or ""
    
    # Game Specific
    cs2_platform = request.GET.get("cs2_platform") or ""
    cs2_faceit_min = request.GET.get("cs2_faceit_min")
    cs2_faceit_max = request.GET.get("cs2_faceit_max")
    cs2_premier_min = request.GET.get("cs2_premier_min")
    cs2_premier_max = request.GET.get("cs2_premier_max")
    valorant_rank = request.GET.get("valorant_rank") or ""
    dota2_rank = request.GET.get("dota2_rank") or ""
    eafc_mode = request.GET.get("eafc_mode") or ""
    dbd_role = request.GET.get("dbd_role") or ""

    if game:
        qs = qs.filter(game__slug=game)
        
        # Apply game specific filters only if the main game is selected
        if game == "cs2":
            try:
                if cs2_faceit_min:
                    qs = qs.filter(req_cs2_faceit_lvl_min__gte=int(cs2_faceit_min))
                if cs2_faceit_max:
                    qs = qs.filter(req_cs2_faceit_lvl_max__lte=int(cs2_faceit_max))
                if cs2_premier_min:
                    qs = qs.filter(req_cs2_premier_rating_min__gte=int(cs2_premier_min))
                if cs2_premier_max:
                    qs = qs.filter(req_cs2_premier_rating_max__lte=int(cs2_premier_max))
            except ValueError:
                pass
        elif game == "valorant":
            if valorant_rank in {choice for choice, _ in Lobby.ValorantRank.choices}:
                qs = qs.filter(req_valorant_rank=valorant_rank)
        elif game == "dota2":
            if dota2_rank in {choice for choice, _ in Lobby.Dota2Rank.choices}:
                qs = qs.filter(req_dota2_rank=dota2_rank)
        elif game == "eafc26":
            if eafc_mode in {choice for choice, _ in Lobby.EafcMode.choices}:
                qs = qs.filter(req_eafc_mode=eafc_mode)
        elif game == "dbd":
            if dbd_role in {choice for choice, _ in Lobby.DbdRole.choices}:
                qs = qs.filter(req_dbd_role=dbd_role)

    if country:
        qs = qs.filter(country=country)
    if role in {choice for choice, _ in Lobby.RequiredRole.choices}:
        qs = qs.filter(required_role=role)
    if mic == "1":
        qs = qs.filter(mic_required=True)

    # Pagination
    qs = qs.order_by("-created_at")
    paginator = Paginator(qs, 12) # 12 per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    my_lobby_ids = set()
    if request.user.is_authenticated:
        my_lobby_ids = set(
            qs.filter(participants__user=request.user).values_list("id", flat=True)
        )

    # Prepare roles dictionary for the frontend
    roles_dict = {}
    for g in game_choices:
        roles_dict[g.slug] = Lobby.required_role_choices_for_game(g.slug)

    # Рахуємо реальні дані з БД
    total_users = User.objects.count()
    total_lobbies = Lobby.objects.filter(status__in=[Lobby.Status.ACTIVE, Lobby.Status.FULL]).count()

    upcoming_tournaments = Tournament.objects.filter(is_active=True, date_time__gte=timezone.now()).order_by('date_time')[:3]

    hot_lobbies = Lobby.objects.select_related("host", "game").filter(status=Lobby.Status.ACTIVE).order_by('-created_at')[:2]

    context = {
        "lobbies": page_obj,  
        "filters": {"game": game, "role": role, "mic": mic, "country": country, "q": q},
        "game_choices": game_choices,
        "valorant_ranks": Lobby.ValorantRank.choices,
        "dota2_ranks": Lobby.Dota2Rank.choices,
        "eafc_modes": Lobby.EafcMode.choices,
        "dbd_roles": Lobby.DbdRole.choices,
        "roles_json": json.dumps(roles_dict),
        "my_lobby_ids": my_lobby_ids,
        "page_obj": page_obj,
        "total_users": total_users,
        "total_lobbies": total_lobbies,
        "upcoming_tournaments": upcoming_tournaments,
        "hot_lobbies": hot_lobbies, # Тепер Python побачить цю змінну!
    }
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Render the lobby list items
        html = render_to_string("lobbies/partials/lobby_list.html", context, request=request)
        # Render the pagination controls
        pagination_html = render_to_string("lobbies/partials/pagination.html", context, request=request)
        return JsonResponse({
            "html": html, 
            "pagination_html": pagination_html,
            "count": paginator.count
        })

    return render(request, "home.html", context)

# ... ТУТ ДАЛІ ТВІЙ КОД ТУРНІРІВ І ДРУЗІВ (ЯКИЙ БУВ) ...


def tournaments_list(request):
    """
    Tournaments Page: list upcoming and ongoing tournaments with AJAX filtering.
    """
    # 1. Отримуємо всі ігри для фільтру
    game_choices = Game.objects.filter(is_active=True).order_by('order')
    
    # 2. Отримуємо всі турніри
    qs = Tournament.objects.filter(is_active=True).select_related('game')
    
    # 3. Фільтрація по грі
    game_slug = request.GET.get("game")
    if game_slug:
        qs = qs.filter(game__slug=game_slug)
        
    # 4. Фільтрація по статусу (Upcoming, Past)
    status_filter = request.GET.get("status", "upcoming") # За замовчуванням Upcoming
    now = timezone.now()
    
    if status_filter == "upcoming":
        qs = qs.filter(date_time__gte=now)
    elif status_filter == "past":
        qs = qs.filter(date_time__lt=now)
        
    # 5. Пошук
    search_query = request.GET.get("search")
    if search_query:
        qs = qs.filter(title__icontains=search_query)

    context = {
        "tournaments": qs,
        "game_choices": game_choices,
        "current_game": game_slug,
        "current_status": status_filter
    }

    # Якщо це AJAX запит (HTMX), повертаємо тільки сітку з турнірами
    if request.headers.get('HX-Request'):
        return render(request, "tournaments/partials/tournament_grid.html", context)

    # Якщо це звичайне завантаження, повертаємо всю сторінку
    return render(request, "tournaments/tournament_list.html", context)


def tournament_detail(request, pk):
    """
    Сторінка деталей конкретного турніру
    """
    tournament = get_object_or_404(Tournament, pk=pk)
    return render(request, "tournaments/tournament_detail.html", {"tournament": tournament})


# ==========================================
# СИСТЕМА ДРУЗІВ (FRIENDS SYSTEM)
# ==========================================

@login_required
def friends_view(request):
    """Головна сторінка друзів"""
    profile = request.user.gamer_profile
    # Отримуємо підтверджених друзів
    friends = profile.friends.all()
    # Отримуємо вхідні запити
    incoming_requests = request.user.received_friend_requests.filter(status='pending')
    
    # Пошук користувачів
    search_query = request.GET.get('q', '')
    search_results = []
    if search_query:
        # Шукаємо по імені, виключаючи самого себе
        search_results = User.objects.filter(username__icontains=search_query).exclude(id=request.user.id)

    context = {
        'friends': friends,
        'incoming_requests': incoming_requests,
        'search_results': search_results,
        'search_query': search_query,
    }
    return render(request, 'users/friends.html', context)

@login_required
def send_friend_request(request, user_id):
    """Надіслати запит у друзі"""
    to_user = get_object_or_404(User, id=user_id)
    
    # Перевірка: чи не додаємо самі себе
    if request.user == to_user:
        messages.warning(request, "You cannot add yourself as a friend.")
        return redirect('friends')
    
    # Перевірка: чи вже в друзях
    if request.user.gamer_profile.friends.filter(id=to_user.gamer_profile.id).exists():
        messages.warning(request, "This user is already in your friends list!")
        return redirect('friends')
        
    freq, created = FriendRequest.objects.get_or_create(
        from_user=request.user, 
        to_user=to_user, 
        defaults={'status': 'pending'}
    )
    
    if created:
        messages.success(request, f"Friend request sent to {to_user.username}!")
    else:
        messages.info(request, "A friend request was already sent to this user.")
        
    return redirect('friends')

@login_required
def accept_friend_request(request, request_id):
    """Прийняти запит у друзі"""
    freq = get_object_or_404(FriendRequest, id=request_id, to_user=request.user, status='pending')
    freq.status = 'accepted'
    freq.save()
    
    # Додаємо профілі один одному в друзі
    request.user.gamer_profile.friends.add(freq.from_user.gamer_profile)
    messages.success(request, f"You and {freq.from_user.username} are now friends!")
    return redirect('friends')

@login_required
def reject_friend_request(request, request_id):
    """Відхилити запит у друзі"""
    freq = get_object_or_404(FriendRequest, id=request_id, to_user=request.user, status='pending')
    freq.status = 'rejected'
    freq.save()
    messages.info(request, "Friend request declined.")
    return redirect('friends')
    
@login_required
def remove_friend(request, user_id):
    """Видалити з друзів"""
    friend_user = get_object_or_404(User, id=user_id)
    request.user.gamer_profile.friends.remove(friend_user.gamer_profile)
    messages.success(request, f"{friend_user.username} removed from your friends.")
    return redirect('friends')

@login_required
def get_notifications(request):
    # Отримуємо всі непрочитані сповіщення для юзера (інвайти в лобі тощо)
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
    
    # ДОДАЄМО: Отримуємо всі вхідні запити в друзі, які ще 'pending'
    friend_requests = FriendRequest.objects.filter(to_user=request.user, status='pending').order_by('-created_at')
    
    return render(request, "lobbies/partials/notifications.html", {
        "notifications": notifications,
        "friend_requests": friend_requests, # Передаємо в шаблон!
    })
@login_required
def get_lobby_players(request, lobby_id):
    """Повертає тільки HTML-шматочок зі списком гравців для HTMX-оновлення"""
    lobby = get_object_or_404(Lobby, id=lobby_id)
    is_participant = lobby.participants.filter(user=request.user).exists()
    
    return render(request, "lobbies/partials/lobby_players.html", {
        "lobby": lobby,
        "is_participant": is_participant,
        "is_htmx": True,  # ❗ ДОДАЛИ ЦЕЙ РЯДОК
    })