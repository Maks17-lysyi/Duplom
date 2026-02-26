import json

from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string

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
    # Optional filtering parameters
    country = request.GET.get("country") or ""
    role = request.GET.get("role") or ""
    mic = request.GET.get("mic") or ""
    
    # Game Specific
    cs2_faceit_min = request.GET.get("cs2_faceit_min")
    cs2_faceit_max = request.GET.get("cs2_faceit_max")
    cs2_premier_min = request.GET.get("cs2_premier_min")
    cs2_premier_max = request.GET.get("cs2_premier_max")
    valorant_rank = request.GET.get("valorant_rank") or ""
    dota2_rank = request.GET.get("dota2_rank") or ""

    if game in {choice for choice, _ in Lobby.Game.choices}:
        qs = qs.filter(game=game)
        
        # Apply game specific filters only if the main game is selected
        if game == Lobby.Game.CS2:
            try:
                if cs2_faceit_min:
                    qs = qs.filter(req_cs2_faceit_lvl__gte=int(cs2_faceit_min))
                if cs2_faceit_max:
                    qs = qs.filter(req_cs2_faceit_lvl__lte=int(cs2_faceit_max))
                if cs2_premier_min:
                    qs = qs.filter(req_cs2_premier_rating__gte=int(cs2_premier_min))
                if cs2_premier_max:
                    qs = qs.filter(req_cs2_premier_rating__lte=int(cs2_premier_max))
            except ValueError:
                pass
        elif game == Lobby.Game.VALORANT:
            if valorant_rank in {choice for choice, _ in Lobby.ValorantRank.choices}:
                qs = qs.filter(req_valorant_rank=valorant_rank)
        elif game == Lobby.Game.DOTA2:
            if dota2_rank in {choice for choice, _ in Lobby.Dota2Rank.choices}:
                qs = qs.filter(req_dota2_rank=dota2_rank)

    if country:
        qs = qs.filter(country=country)
    if role in {choice for choice, _ in Lobby.RequiredRole.choices}:
        qs = qs.filter(required_role=role)
    if mic == "1":
        qs = qs.filter(mic_required=True)

    my_lobby_ids = set()
    if request.user.is_authenticated:
        my_lobby_ids = set(
            qs.filter(participants__user=request.user).values_list("id", flat=True)
        )

    # Prepare roles dictionary for the frontend
    roles_dict = {}
    for g, _ in Lobby.Game.choices:
        roles_dict[g] = Lobby.required_role_choices_for_game(g)

    context = {
        "lobbies": qs,
        "filters": {"game": game, "role": role, "mic": mic, "country": country},
        "game_choices": Lobby.Game.choices,
        "valorant_ranks": Lobby.ValorantRank.choices,
        "dota2_ranks": Lobby.Dota2Rank.choices,
        "roles_json": json.dumps(roles_dict),
        "my_lobby_ids": my_lobby_ids,
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string("lobbies/partials/lobby_list.html", context, request=request)
        return JsonResponse({"html": html, "count": qs.count()})

    return render(request, "home.html", context)
