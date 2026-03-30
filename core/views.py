import json

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q  # <--- ВАЖЛИВО ДЛЯ ПОШУКУ
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone

# ❗ Залишаємо тільки правильні імпорти без дублікатів
from lobbies.models import Game, Lobby, Tournament
from users.models import DirectMessage, FriendRequest, GamerProfile, Notification

User = get_user_model()


def home(request):
    """
    Dashboard: list active lobbies + filters.
    """
    game_choices = Game.objects.filter(is_active=True).order_by("order")
    qs = (
        Lobby.objects.select_related("host")
        .prefetch_related("participants__user")
        .filter(status__in=[Lobby.Status.ACTIVE, Lobby.Status.FULL])
    )

    # --- ПОШУК ПО НАЗВІ/ХОСТУ ---
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(title__icontains=q) | Q(game__name__icontains=q) | Q(host__username__icontains=q)
        )

    game = request.GET.get("game") or ""
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
    paginator = Paginator(qs, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    my_lobby_ids = set()
    if request.user.is_authenticated:
        my_lobby_ids = set(qs.filter(participants__user=request.user).values_list("id", flat=True))

    roles_dict = {}
    for g in game_choices:
        roles_dict[g.slug] = Lobby.required_role_choices_for_game(g.slug)

    total_users = User.objects.count()
    total_lobbies = Lobby.objects.filter(
        status__in=[Lobby.Status.ACTIVE, Lobby.Status.FULL]
    ).count()
    upcoming_tournaments = Tournament.objects.filter(
        is_active=True, date_time__gte=timezone.now()
    ).order_by("date_time")[:3]
    hot_lobbies = (
        Lobby.objects.select_related("host", "game")
        .filter(status=Lobby.Status.ACTIVE)
        .order_by("-created_at")[:2]
    )

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
        "hot_lobbies": hot_lobbies,
    }

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string("lobbies/partials/lobby_list.html", context, request=request)
        pagination_html = render_to_string(
            "lobbies/partials/pagination.html", context, request=request
        )
        return JsonResponse(
            {"html": html, "pagination_html": pagination_html, "count": paginator.count}
        )

    return render(request, "home.html", context)


def tournaments_list(request):
    """
    Tournaments Page: list upcoming and ongoing tournaments with AJAX filtering.
    """
    game_choices = Game.objects.filter(is_active=True).order_by("order")
    qs = Tournament.objects.filter(is_active=True).select_related("game")

    game_slug = request.GET.get("game")
    if game_slug:
        qs = qs.filter(game__slug=game_slug)

    status_filter = request.GET.get("status", "upcoming")
    now = timezone.now()

    if status_filter == "upcoming":
        qs = qs.filter(date_time__gte=now)
    elif status_filter == "past":
        qs = qs.filter(date_time__lt=now)

    search_query = request.GET.get("search")
    if search_query:
        qs = qs.filter(title__icontains=search_query)

    context = {
        "tournaments": qs,
        "game_choices": game_choices,
        "current_game": game_slug,
        "current_status": status_filter,
    }

    if request.headers.get("HX-Request"):
        return render(request, "tournaments/partials/tournament_grid.html", context)

    return render(request, "tournaments/tournament_list.html", context)


# ==========================================
# ❗ ГЛОБАЛЬНИЙ ПОШУК
# ==========================================
def search_results(request):
    """
    Global Search Page: Finds users by username and active lobbies by title/game.
    """
    query = request.GET.get("q", "").strip()

    users = []
    lobbies = []

    if query:
        # 1. Шукаємо юзерів (по username), виключаємо самого себе
        users_qs = User.objects.filter(username__icontains=query)
        if request.user.is_authenticated:
            users_qs = users_qs.exclude(id=request.user.id)
        users = users_qs[:20]  # Ліміт 20 юзерів, щоб не грузити базу

        # 2. Шукаємо активні лобі (по title або по назві гри)
        lobbies = Lobby.objects.filter(
            Q(title__icontains=query) | Q(game__name__icontains=query), status=Lobby.Status.ACTIVE
        ).select_related("game", "host")[
            :20
        ]  # Ліміт 20 сквадів

    context = {
        "query": query,
        "users": users,
        "lobbies": lobbies,
    }
    return render(request, "search_results.html", context)


def tournament_detail(request, pk):
    """Сторінка деталей конкретного турніру"""
    tournament = get_object_or_404(Tournament, pk=pk)
    return render(request, "tournaments/tournament_detail.html", {"tournament": tournament})


# ==========================================
# СИСТЕМА ДРУЗІВ (FRIENDS SYSTEM) ТА ПУБЛІЧНИЙ ПРОФІЛЬ
# ==========================================


@login_required
def public_profile(request, username):
    """Сторінка публічного профілю іншого гравця"""
    target_user = get_object_or_404(User, username=username)

    # Якщо юзер клікнув на свій власний профіль в пошуку — кидаємо його на його приватну сторінку
    if request.user == target_user:
        return redirect("profile")

    profile = target_user.gamer_profile

    # Перевіряємо статус дружби
    is_friend = request.user.gamer_profile.friends.filter(id=profile.id).exists()

    # Перевіряємо, чи є вже відправлені або отримані запити
    request_sent = FriendRequest.objects.filter(
        from_user=request.user, to_user=target_user, status="pending"
    ).exists()
    request_received = FriendRequest.objects.filter(
        from_user=target_user, to_user=request.user, status="pending"
    ).first()

    # Рахуємо статистику для відображення
    hosted_count = target_user.hosted_lobbies.count()
    joined_count = target_user.lobby_participations.count()

    context = {
        "target_user": target_user,
        "profile": profile,
        "is_friend": is_friend,
        "request_sent": request_sent,
        "request_received": request_received,
        "stats": {"hosted": hosted_count, "joined": joined_count},
    }
    return render(request, "users/public_profile.html", context)


@login_required
def direct_chat(request, username):
    target_user = get_object_or_404(User, username=username)
    
    # 1. ОБРОБКА ВІДПРАВКИ (POST)
    if request.method == "POST":
        content = request.POST.get("content")
        if content:
            # Створюємо повідомлення
            DirectMessage.objects.create(sender=request.user, receiver=target_user, content=content)
            
            # ⚡ АНТИ-СПАМ: ВИДАЛЯЄМО СТАРІ СПОВІЩЕННЯ ВІД ЦЬОГО Ж ВІДПРАВНИКА
            Notification.objects.filter(
                recipient=target_user,
                sender=request.user, 
                notification_type="direct_message"
            ).delete()

            # СТВОРЮЄМО ОДНЕ НОВЕ, СВІЖЕ СПОВІЩЕННЯ
            Notification.objects.create(
                recipient=target_user,
                sender=request.user, 
                notification_type="direct_message",
                message=f"New message from {request.user.username}: {content[:30]}..." 
            )
            
    # 2. ЛОГІКА ДЛЯ ЗВУКУ ОТРИМАННЯ
    unread_messages = DirectMessage.objects.filter(sender=target_user, receiver=request.user, is_read=False)
    has_new_messages = unread_messages.exists()
    
    if has_new_messages:
        unread_messages.update(is_read=True)

    # 3. ВИВІД ЧАТУ
    messages = DirectMessage.objects.filter(
        Q(sender=request.user, receiver=target_user) | Q(sender=target_user, receiver=request.user)
    ).order_by('created_at')

    # ❗ ОСЬ ВІН - ПРАВИЛЬНИЙ ШЛЯХ ЗІ СКРІНШОТУ
    return render(request, "lobbies/partials/chat_messages.html", {
        "messages": messages,
        "target_user": target_user,
        "has_new_messages": has_new_messages, 
    })

@login_required
def friends_view(request):
    """Головна сторінка друзів"""
    profile = request.user.gamer_profile
    friends = profile.friends.all()
    incoming_requests = request.user.received_friend_requests.filter(status="pending")

    sent_requests_ids = request.user.sent_friend_requests.filter(status="pending").values_list(
        "to_user_id", flat=True
    )

    search_query = request.GET.get("q", "")
    search_results = []
    if search_query:
        search_results = User.objects.filter(username__icontains=search_query).exclude(
            id=request.user.id
        )

    context = {
        "friends": friends,
        "incoming_requests": incoming_requests,
        "search_results": search_results,
        "search_query": search_query,
        "sent_requests_ids": sent_requests_ids,
    }
    return render(request, "users/friends.html", context)


@login_required
def send_friend_request(request, user_id):
    """Надіслати запит у друзі"""
    to_user = get_object_or_404(User, id=user_id)

    if request.user == to_user:
        messages.warning(request, "You cannot add yourself.")
        return redirect("friends")

    if request.user.gamer_profile.friends.filter(id=to_user.gamer_profile.id).exists():
        messages.warning(request, "This user is already your friend!")
        return redirect("friends")

    freq, created = FriendRequest.objects.get_or_create(from_user=request.user, to_user=to_user)

    if freq.status != "pending":
        freq.status = "pending"
        freq.save()

    messages.success(request, f"Friend request sent to {to_user.username}!")
    return redirect(request.META.get("HTTP_REFERER", "friends"))


@login_required
def accept_friend_request(request, request_id):
    """Прийняти запит у друзі та надіслати сповіщення"""
    freq = get_object_or_404(FriendRequest, id=request_id, to_user=request.user, status="pending")
    freq.status = "accepted"
    freq.save()

    request.user.gamer_profile.friends.add(freq.from_user.gamer_profile)

    Notification.objects.create(
        recipient=freq.from_user,
        notification_type="system",
        message=f"{request.user.username} accepted your friend request! You are now friends.",
    )

    Notification.objects.create(
        recipient=request.user,
        notification_type="system",
        message=f"You and {freq.from_user.username} are now friends!",
    )

    messages.success(request, f"You and {freq.from_user.username} are now friends!")
    return redirect(request.META.get("HTTP_REFERER", "home"))


@login_required
def reject_friend_request(request, request_id):
    """Відхилити запит у друзі"""
    freq = get_object_or_404(FriendRequest, id=request_id, to_user=request.user, status="pending")
    freq.status = "rejected"
    freq.save()
    messages.info(request, "Friend request declined.")
    return redirect(request.META.get("HTTP_REFERER", "home"))


@login_required
def remove_friend(request, user_id):
    """Видалити з друзів"""
    friend_user = get_object_or_404(User, id=user_id)
    request.user.gamer_profile.friends.remove(friend_user.gamer_profile)
    messages.success(request, f"{friend_user.username} removed from your friends.")
    return redirect(request.META.get("HTTP_REFERER", "friends"))


@login_required
def get_notifications(request):
    """HTML для дзвіночка та тоастів"""
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by(
        "-created_at"
    )
    friend_requests = FriendRequest.objects.filter(to_user=request.user, status="pending").order_by(
        "-created_at"
    )
    
    # ❗ ДОДАНО: Перевірка для звуку глобальних сповіщень
    has_new_notifs = notifications.exists()

    return render(
        request,
        "lobbies/partials/notifications.html",
        {
            "notifications": notifications,
            "friend_requests": friend_requests,
            "has_new_notifs": has_new_notifs, # 👈 Тепер звук буде працювати!
        },
    )


@login_required
def get_lobby_players(request, lobby_id):
    """Повертає тільки HTML-шматочок зі списком гравців для HTMX-оновлення"""
    lobby = get_object_or_404(Lobby, id=lobby_id)
    is_participant = lobby.participants.filter(user=request.user).exists()

    return render(
        request,
        "lobbies/partials/lobby_players.html",
        {
            "lobby": lobby,
            "is_participant": is_participant,
            "is_htmx": True,
        },
    )


@login_required
def invite_to_lobby(request, lobby_id, user_id):
    """Запросити друга у своє лобі"""
    lobby = get_object_or_404(Lobby, id=lobby_id)
    target_user = get_object_or_404(User, id=user_id)

    # Створюємо сповіщення для друга
    Notification.objects.create(
        recipient=target_user,
        sender=request.user,
        notification_type="lobby_invite",
        lobby_id=lobby.id,
        message=f"{request.user.username} invited you to join squad: {getattr(lobby, 'title', getattr(lobby, 'name', 'Lobby'))}",
    )

    messages.success(request, f"Invite sent to {target_user.username}!")
    return redirect(request.META.get("HTTP_REFERER", "home"))