from django.shortcuts import render

from lobbies.models import Lobby


def home(request):
    """
    Dashboard: list active lobbies + filters.
    """
    qs = (
        Lobby.objects.select_related("host")
        .prefetch_related("participants__user")
        .filter(status__in=[Lobby.Status.ACTIVE, Lobby.Status.FULL])
    )

    game = request.GET.get("game") or ""
    rank = request.GET.get("rank") or ""
    role = request.GET.get("role") or ""
    mic = request.GET.get("mic") or ""

    if game in {choice for choice, _ in Lobby.Game.choices}:
        qs = qs.filter(game=game)
    if rank in {choice for choice, _ in Lobby.RequiredRank.choices}:
        qs = qs.filter(required_rank=rank)
    if role in {choice for choice, _ in Lobby.RequiredRole.choices}:
        qs = qs.filter(required_role=role)
    if mic == "1":
        qs = qs.filter(mic_required=True)

    my_lobby_ids = set()
    if request.user.is_authenticated:
        my_lobby_ids = set(
            qs.filter(participants__user=request.user).values_list("id", flat=True)
        )

    context = {
        "lobbies": qs,
        "filters": {"game": game, "rank": rank, "role": role, "mic": mic},
        "game_choices": Lobby.Game.choices,
        "rank_choices": Lobby.RequiredRank.choices,
        "role_choices": Lobby.RequiredRole.choices,
        "my_lobby_ids": my_lobby_ids,
    }
    return render(request, "home.html", context)
