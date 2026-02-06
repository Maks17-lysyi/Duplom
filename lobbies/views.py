from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from .forms import LobbyForm
from .forms import LobbyForm
from .models import ChatMessage, Lobby, LobbyParticipant


def lobby_detail(request, lobby_id: int):
    lobby = get_object_or_404(
        Lobby.objects.select_related("host").prefetch_related("participants__user"),
        pk=lobby_id,
    )

    is_participant = False
    if request.user.is_authenticated:
        is_participant = lobby.participants.filter(user=request.user).exists()

    reveal_host_contacts = is_participant and request.user.is_authenticated
    host_profile = getattr(lobby.host, "gamer_profile", None)

    context = {
        "lobby": lobby,
        "participants": lobby.participants.all(),
        "is_participant": is_participant,
        "reveal_host_contacts": reveal_host_contacts,
        "host_profile": host_profile,
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
        lobby = (
            Lobby.objects.select_for_update()
            .select_related("host")
            .get(pk=lobby_id)
        )

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

    lobby.save(update_fields=["status"])
    messages.success(request, "Lobby ended.")
    return redirect("lobby_detail", lobby_id=lobby_id)


@login_required
def lobby_chat_messages(request, lobby_id: int):
    lobby = get_object_or_404(Lobby, pk=lobby_id)
    # Show last 50 messages
    chat_messages = lobby.messages.select_related("sender").order_by("created_at")[
        :50
    ]
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
        # Silently fail or return error, for now just redirect
        return redirect("lobby_detail", lobby_id=lobby_id)

    content = request.POST.get("content", "").strip()
    if content:
        ChatMessage.objects.create(lobby=lobby, sender=request.user, content=content)

    return redirect("lobby_chat_messages", lobby_id=lobby_id)

