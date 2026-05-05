from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from users.models import Notification

from .forms import LobbyForm
# ❗ ОНОВЛЕНИЙ ІМПОРТ: додали Tournament, Match, Team
from .models import ChatMessage, Lobby, LobbyParticipant, Tournament, Match, Team, GameServer
# ❗ НОВИЙ ІМПОРТ: функція генерації сітки
from .services import generate_tournament_bracket

User = get_user_model()


def lobby_detail(request, lobby_id: int):
    lobby = get_object_or_404(
        Lobby.objects.select_related("host").prefetch_related("participants__user"),
        pk=lobby_id,
    )

    is_participant = False
    friends_to_invite = []

    if request.user.is_authenticated:
        is_participant = lobby.participants.filter(user=request.user).exists()

        if is_participant and lobby.status == Lobby.Status.ACTIVE:
            current_participant_ids = lobby.participants.values_list("user_id", flat=True)
            if hasattr(request.user, "gamer_profile"):
                friends_profiles = request.user.gamer_profile.friends.exclude(
                    user_id__in=current_participant_ids
                )
                friends_to_invite = [p.user for p in friends_profiles]

    reveal_host_contacts = is_participant and request.user.is_authenticated
    host_profile = getattr(lobby.host, "gamer_profile", None)

    context = {
        "lobby": lobby,
        "participants": lobby.participants.all(),
        "is_participant": is_participant,
        "reveal_host_contacts": reveal_host_contacts,
        "host_profile": host_profile,
        "friends_to_invite": friends_to_invite,
    }
    return render(request, "lobbies/lobby_detail.html", context)


@login_required
def lobby_create(request):
    if request.method == "POST":
        form = LobbyForm(request.POST)
        if form.is_valid():
            lobby = form.save(commit=False)
            lobby.host = request.user
            try:
                lobby.save()
            except IntegrityError:
                messages.error(
                    request,
                    "You already host an active lobby. End it before creating a new one.",
                )
                return redirect("profile")
            messages.success(request, "Lobby created.")
            return redirect("lobby_detail", lobby_id=lobby.id)
    else:
        form = LobbyForm()

    return render(request, "lobbies/lobby_form.html", {"form": form})


@login_required
def lobby_join(request, lobby_id: int):
    if request.method != "POST":
        raise Http404

    with transaction.atomic():
        lobby = Lobby.objects.select_for_update().select_related("host").get(pk=lobby_id)

        if lobby.status == Lobby.Status.ENDED:
            messages.error(request, "This lobby has ended.")
            return redirect("lobby_detail", lobby_id=lobby.id)

        if LobbyParticipant.objects.filter(lobby=lobby, user=request.user).exists():
            messages.info(request, "You're already in this lobby.")
            return redirect("lobby_detail", lobby_id=lobby.id)

        if lobby.participants.count() >= lobby.slots_total:
            messages.error(request, "This lobby is full.")
            return redirect("lobby_detail", lobby_id=lobby.id)

        LobbyParticipant.objects.create(lobby=lobby, user=request.user)

    messages.success(request, "Joined lobby. Host contact info is now visible.")
    return redirect("lobby_detail", lobby_id=lobby_id)


@login_required
def lobby_leave(request, lobby_id: int):
    if request.method != "POST":
        raise Http404

    lobby = get_object_or_404(Lobby, pk=lobby_id)

    if lobby.host_id == request.user.id:
        messages.error(
            request,
            "You're the host. End the lobby instead of leaving.",
        )
        return redirect("lobby_detail", lobby_id=lobby_id)

    LobbyParticipant.objects.filter(lobby=lobby, user=request.user).delete()
    messages.success(request, "You left the lobby.")
    return redirect("lobby_detail", lobby_id=lobby_id)


@login_required
def lobby_end(request, lobby_id: int):
    if request.method != "POST":
        raise Http404

    lobby = get_object_or_404(Lobby, pk=lobby_id)
    if lobby.host_id != request.user.id:
        messages.error(request, "Only the host can end this lobby.")
        return redirect("lobby_detail", lobby_id=lobby_id)

    lobby.status = Lobby.Status.ENDED
    lobby.save(update_fields=["status"])
    messages.success(request, "Lobby ended.")
    return redirect("lobby_detail", lobby_id=lobby_id)


@login_required
def invite_friend(request, lobby_id: int, friend_id: int):
    if request.method != "POST":
        raise Http404

    lobby = get_object_or_404(Lobby, pk=lobby_id)
    friend = get_object_or_404(User, pk=friend_id)

    if lobby.status != Lobby.Status.ACTIVE:
        messages.error(request, "This lobby is not active.")
        return redirect("lobby_detail", lobby_id=lobby_id)

    if lobby.participants.count() >= lobby.slots_total:
        messages.error(request, "This lobby is full.")
        return redirect("lobby_detail", lobby_id=lobby_id)

    if not lobby.participants.filter(user=request.user).exists():
        messages.error(request, "You must be in the lobby to invite friends.")
        return redirect("lobby_detail", lobby_id=lobby_id)

    if lobby.participants.filter(user=friend).exists():
        messages.info(request, f"{friend.username} is already in the squad.")
        return redirect("lobby_detail", lobby_id=lobby_id)

    invite_exists = Notification.objects.filter(
        recipient=friend,
        sender=request.user,
        notification_type="lobby_invite",
        lobby_id=lobby.id,
        is_read=False,
    ).exists()

    if invite_exists:
        messages.info(request, f"You already sent an invite to {friend.username}.")
    else:
        Notification.objects.create(
            recipient=friend,
            sender=request.user,
            notification_type="lobby_invite",
            lobby_id=lobby.id,
            message=f"invited you to join squad: {lobby.title}",
        )
        messages.success(request, f"Invite sent to {friend.username}!")

    return redirect("lobby_detail", lobby_id=lobby_id)


@login_required
def accept_lobby_invite(request, notification_id: int):
    if request.method != "POST":
        raise Http404

    notification = get_object_or_404(Notification, pk=notification_id, recipient=request.user)
    lobby = get_object_or_404(Lobby, pk=notification.lobby_id)

    if lobby.participants.count() < lobby.slots_total and lobby.status == Lobby.Status.ACTIVE:
        LobbyParticipant.objects.get_or_create(lobby=lobby, user=request.user)
        messages.success(request, f"You joined {lobby.title}!")

        ChatMessage.objects.create(
            lobby=lobby,
            sender=request.user,
            content=f"⚡ {request.user.username} joined via invite from {notification.sender.username}!",
        )
    else:
        messages.error(request, "Lobby is already full or ended.")

    notification.is_read = True
    notification.save()

    return redirect("lobby_detail", lobby_id=lobby.id)


@login_required
def reject_lobby_invite(request, notification_id: int):
    if request.method != "POST":
        raise Http404

    notification = get_object_or_404(Notification, pk=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()

    messages.info(request, "Invite declined.")
    return redirect(request.META.get("HTTP_REFERER", "home"))


@login_required
def lobby_chat_messages(request, lobby_id: int):
    lobby = get_object_or_404(Lobby, pk=lobby_id)
    chat_messages = lobby.messages.select_related("sender").order_by("created_at")[:50]
    return render(
        request,
        "lobbies/partials/chat_messages.html",
        {"messages": chat_messages, "user": request.user},
    )


@login_required
def lobby_chat_send(request, lobby_id: int):
    if request.method != "POST":
        return redirect("lobby_detail", lobby_id=lobby_id)

    lobby = get_object_or_404(Lobby, pk=lobby_id)
    is_participant = lobby.participants.filter(user=request.user).exists()
    if not is_participant and lobby.host != request.user:
        return redirect("lobby_detail", lobby_id=lobby_id)

    content = request.POST.get("content", "").strip()
    if content:
        ChatMessage.objects.create(lobby=lobby, sender=request.user, content=content)

    return redirect("lobby_chat_messages", lobby_id=lobby_id)


# ==========================================
# В'ЮШКИ ДЛЯ ТУРНІРІВ (ДОДАНО ДЛЯ ДИПЛОМУ)
# ==========================================

def tournament_list(request):
    """
    Показує список всіх турнірів на сайті.
    """
    tournaments = Tournament.objects.all().order_by('-date_time')
    return render(request, 'tournaments/tournament_list.html', {'tournaments': tournaments})


def tournament_detail(request, tournament_id):
    """
    Сторінка конкретного турніру (опис, правила, сітка).
    """
    tournament = get_object_or_404(Tournament, pk=tournament_id)
    
    # Витягуємо всі матчі турніру, щоб намалювати сітку
    matches = tournament.matches.all().order_by('-round_number')
    
    context = {
        'tournament': tournament,
        'matches': matches,
        'registered_teams_count': tournament.registered_teams.count(),
    }
    return render(request, 'tournaments/tournament_detail.html', context)


@login_required
def tournament_start(request, tournament_id):
    """
    Кнопка, яку тисне Організатор, щоб згенерувати сітку і почати турнір.
    """
    if request.method != "POST":
        raise Http404

    tournament = get_object_or_404(Tournament, pk=tournament_id)

    # Тільки організатор може почати турнір
    if request.user != tournament.organizer:
        messages.error(request, "Тільки організатор може почати цей турнір.")
        return redirect('tournament_detail', tournament_id=tournament.id)

    # Викликаємо нашу магічну функцію з services.py
    success, msg = generate_tournament_bracket(tournament)
    
    if success:
        messages.success(request, msg)
    else:
        messages.error(request, msg)

    return redirect('tournament_detail', tournament_id=tournament.id)

@login_required
def tournament_join(request, tournament_id):
    """
    Швидка реєстрація на турнір.
    Автоматично створює команду для юзера (якщо її немає) і записує на турнір.
    """
    if request.method != "POST":
        raise Http404

    tournament = get_object_or_404(Tournament, pk=tournament_id)

    # Перевіряємо, чи відкрита реєстрація
    if tournament.status != Tournament.Status.REGISTRATION:
        messages.error(request, "Реєстрація на цей турнір вже закрита або він завершився.")
        return redirect('tournament_detail', tournament_id=tournament.id)

    # Перевіряємо ліміт команд
    if tournament.registered_teams.count() >= tournament.max_teams:
        messages.error(request, "Турнір вже повністю заповнений!")
        return redirect('tournament_detail', tournament_id=tournament.id)

    # Лайфхак для диплому: автоматично створюємо тіму для гравця
    team_name = f"Team {request.user.username}"
    team, created = Team.objects.get_or_create(
        name=team_name,
        defaults={'captain': request.user}
    )

    # Записуємо тіму в турнір
    if team in tournament.registered_teams.all():
        messages.info(request, "Ви вже зареєстровані на цей турнір!")
    else:
        tournament.registered_teams.add(team)
        messages.success(request, f"Ви успішно зареєструвалися як {team.name}!")

    return redirect('tournament_detail', tournament_id=tournament.id)

# ==========================================
# В'ЮШКИ ДЛЯ МАТЧІВ (СЕРВЕРИ ТА СІТКА)
# ==========================================

def match_detail(request, match_id):
    """Сторінка конкретного матчу (IP сервера, команди, кнопка перемоги)"""
    match = get_object_or_404(Match, pk=match_id)
    return render(request, 'tournaments/match_detail.html', {'match': match})

@login_required
def match_assign_server(request, match_id):
    """Організатор видає вільний сервер для матчу"""
    if request.method != "POST":
        raise Http404

    match = get_object_or_404(Match, pk=match_id)
    
    if request.user != match.tournament.organizer:
        messages.error(request, "Тільки організатор може видати сервер.")
        return redirect('match_detail', match_id=match.id)

    # Шукаємо перший вільний сервер у базі
    free_server = GameServer.objects.filter(is_busy=False).first()
    
    if free_server:
        free_server.is_busy = True
        free_server.save()
        
        match.server = free_server
        match.status = Match.Status.READY
        match.save()
        messages.success(request, f"Сервер {free_server.ip_address} успішно видано для цього матчу!")
    else:
        messages.error(request, "На жаль, зараз немає вільних серверів. Додайте їх в адмін-панелі.")
        
    return redirect('match_detail', match_id=match.id)

@login_required
def match_set_winner(request, match_id):
    """Організатор вказує переможця та фінальний рахунок"""
    if request.method != "POST":
        raise Http404

    match = get_object_or_404(Match, pk=match_id)
    
    if request.user != match.tournament.organizer:
        messages.error(request, "Тільки організатор може завершити матч.")
        return redirect('match_detail', match_id=match.id)

    winner_id = request.POST.get('winner_id')
    
    # ❗ НОВЕ: Отримуємо рахунок з форми
    score1 = request.POST.get('score_team1', 0)
    score2 = request.POST.get('score_team2', 0)

    winner = get_object_or_404(Team, pk=winner_id)

    # Записуємо дані
    match.winner = winner
    match.score_team1 = int(score1) if score1 else 0
    match.score_team2 = int(score2) if score2 else 0
    match.status = Match.Status.FINISHED
    match.save()

    # Звільняємо сервер
    if match.server:
        match.server.is_busy = False
        match.server.save()

    # Просуваємо переможця у наступний раунд
    if match.next_match:
        next_m = match.next_match
        if not next_m.team1:
            next_m.team1 = winner
        elif not next_m.team2:
            next_m.team2 = winner
        next_m.save()

    messages.success(request, f"Матч завершено! Рахунок: {match.score_team1} - {match.score_team2}.")
    return redirect('tournament_detail', tournament_id=match.tournament.id)