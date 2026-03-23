from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import get_user_model
from users.models import Notification
from .forms import LobbyForm
from .models import ChatMessage, Lobby, LobbyParticipant

User = get_user_model()


def lobby_detail(request, lobby_id: int):
    lobby = get_object_or_404(
        Lobby.objects.select_related("host").prefetch_related("participants__user"),
        pk=lobby_id,
    )

    is_participant = False
    friends_to_invite = []  # Список друзів, яких можна запросити

    if request.user.is_authenticated:
        is_participant = lobby.participants.filter(user=request.user).exists()

        # Якщо ми учасник і лобі не заповнене/завершене, формуємо список друзів для запрошення
        if is_participant and lobby.status == Lobby.Status.ACTIVE:
            # Отримуємо ID всіх, хто вже в лобі
            current_participant_ids = lobby.participants.values_list("user_id", flat=True)
            # Отримуємо друзів юзера (через GamerProfile), виключаючи тих, хто вже в лобі
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
        "friends_to_invite": friends_to_invite,  # Передаємо друзів в шаблон
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

        # Already in?
        if LobbyParticipant.objects.filter(lobby=lobby, user=request.user).exists():
            messages.info(request, "You're already in this lobby.")
            return redirect("lobby_detail", lobby_id=lobby.id)

        # Full?
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


# --- ОНОВЛЕНА ФУНКЦІЯ: ЗАПРОСИТИ ДРУГА ---
@login_required
def invite_friend(request, lobby_id: int, friend_id: int):
    if request.method != "POST":
        raise Http404

    lobby = get_object_or_404(Lobby, pk=lobby_id)
    friend = get_object_or_404(User, pk=friend_id)

    # Перевірки
    if lobby.status != Lobby.Status.ACTIVE:
        messages.error(request, "This lobby is not active.")
        return redirect("lobby_detail", lobby_id=lobby_id)

    if lobby.participants.count() >= lobby.slots_total:
        messages.error(request, "This lobby is full.")
        return redirect("lobby_detail", lobby_id=lobby_id)

    if not lobby.participants.filter(user=request.user).exists():
        messages.error(request, "You must be in the lobby to invite friends.")
        return redirect("lobby_detail", lobby_id=lobby_id)

    # Перевіряємо, чи друг ВЖЕ в лобі
    if lobby.participants.filter(user=friend).exists():
        messages.info(request, f"{friend.username} is already in the squad.")
        return redirect("lobby_detail", lobby_id=lobby_id)

    # Перевіряємо, чи ми вже кидали йому інвайт, який він ще не прочитав
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
        # СТВОРЮЄМО ПОВІДОМЛЕННЯ В БАЗІ ДАНИХ (ДЛЯ ДЗВІНОЧКА)
        Notification.objects.create(
            recipient=friend,
            sender=request.user,
            notification_type="lobby_invite",
            lobby_id=lobby.id,
            message=f"invited you to join squad: {lobby.title}",
        )
        messages.success(request, f"Invite sent to {friend.username}!")

    return redirect("lobby_detail", lobby_id=lobby_id)


# --- НОВІ ФУНКЦІЇ: ПРИЙНЯТИ АБО ВІДХИЛИТИ ЗАПРОШЕННЯ ---
@login_required
def accept_lobby_invite(request, notification_id: int):
    if request.method != "POST":
        raise Http404

    notification = get_object_or_404(Notification, pk=notification_id, recipient=request.user)
    lobby = get_object_or_404(Lobby, pk=notification.lobby_id)

    # Перевіряємо, чи є ще місця в лобі
    if lobby.participants.count() < lobby.slots_total and lobby.status == Lobby.Status.ACTIVE:
        # Додаємо гравця в лобі
        LobbyParticipant.objects.get_or_create(lobby=lobby, user=request.user)
        messages.success(request, f"You joined {lobby.title}!")

        # Повідомлення в чат лобі
        ChatMessage.objects.create(
            lobby=lobby,
            sender=request.user,
            content=f"⚡ {request.user.username} joined via invite from {notification.sender.username}!",
        )
    else:
        messages.error(request, "Lobby is already full or ended.")

    # Позначаємо сповіщення як прочитане
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

    # Повертаємо юзера туди, де він був (або на головну)
    return redirect(request.META.get("HTTP_REFERER", "home"))


@login_required
def lobby_chat_messages(request, lobby_id: int):
    lobby = get_object_or_404(Lobby, pk=lobby_id)
    # Show last 50 messages
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
    # Ensure user is participant or host
    is_participant = lobby.participants.filter(user=request.user).exists()
    if not is_participant and lobby.host != request.user:
        return redirect("lobby_detail", lobby_id=lobby_id)

    content = request.POST.get("content", "").strip()
    if content:
        ChatMessage.objects.create(lobby=lobby, sender=request.user, content=content)

    return redirect("lobby_chat_messages", lobby_id=lobby_id)
