from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from lobbies.models import Lobby, LobbyParticipant

from .forms import GamerProfileForm, RegisterForm, UserUpdateForm
from .models import GamerProfile, Notification


def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(request, "Welcome to SquadUp! Your account is ready.")
            return redirect("profile_edit")
    else:
        form = RegisterForm()

    return render(request, "users/register.html", {"form": form})


@login_required
def profile_view(request):
    profile, _ = GamerProfile.objects.get_or_create(user=request.user)

    hosted_active = (
        Lobby.objects.filter(host=request.user, status=Lobby.Status.ACTIVE)
        .select_related("host")
        .first()
    )
    current_lobbies = (
        Lobby.objects.filter(
            participants__user=request.user,
            status__in=[Lobby.Status.ACTIVE, Lobby.Status.FULL],
        )
        .distinct()
        .order_by("-created_at")
    )

    # Simple “history” (ended lobbies the user participated in)
    ended_lobbies = (
        Lobby.objects.filter(participants__user=request.user, status=Lobby.Status.ENDED)
        .distinct()
        .order_by("-created_at")[:10]
    )

    joined_count = LobbyParticipant.objects.filter(user=request.user).count()
    hosted_count = Lobby.objects.filter(host=request.user).count()

    context = {
        "profile": profile,
        "hosted_active": hosted_active,
        "current_lobbies": current_lobbies,
        "ended_lobbies": ended_lobbies,
        "stats": {"joined": joined_count, "hosted": hosted_count},
    }
    return render(request, "users/profile.html", context)


@login_required
def profile_edit(request):
    profile, _ = GamerProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = GamerProfileForm(request.POST, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profile updated.")
            return redirect("profile")
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = GamerProfileForm(instance=profile)

    return render(
        request,
        "users/profile_edit.html",
        {"user_form": user_form, "profile_form": profile_form},
    )


# ==========================================
# ❗ ФІКС ДЛЯ СПОВІЩЕНЬ (ВБИВАЄ ЇХ В БАЗІ) ❗
# ==========================================
@login_required
def read_notification(request, notif_id):
    """Позначає сповіщення лобі як прочитане і перекидає куди треба"""
    notif = get_object_or_404(Notification, id=notif_id, recipient=request.user)
    notif.is_read = True
    notif.save()

    # Якщо ми натиснули Accept, в URL буде ?lobby=...
    lobby_id = request.GET.get("lobby")
    if lobby_id:
        return redirect("lobby_detail", lobby_id)  # Перекидаємо в лобі!

    # Якщо ми натиснули Dismiss - просто оновлюємо сторінку і залишаємось на місці
    return redirect(request.META.get("HTTP_REFERER", "home"))
