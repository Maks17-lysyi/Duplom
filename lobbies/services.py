import random
import math
from .models import Match, Tournament

def generate_tournament_bracket(tournament):
    """
    Генерує сітку Single Elimination (на виліт) для турніру.
    """
    # 1. Перевіряємо, чи сітка вже не створена (щоб не створити дублікати)
    if tournament.matches.exists():
        return False, "Сітка для цього турніру вже згенерована."

    teams = list(tournament.registered_teams.all())
    num_teams = len(teams)

    # 2. Перевіряємо, чи набралася потрібна кількість команд
    if num_teams != tournament.max_teams:
        return False, f"Для старту потрібно {tournament.max_teams} команд, а зараз зареєстровано {num_teams}."

    # 3. Перемішуємо команди випадковим чином (жеребкування)
    random.shuffle(teams)
    
    # Визначаємо кількість раундів (для 8 команд це буде 3 раунди: 1/4, 1/2, Фінал)
    total_rounds = int(math.log2(num_teams))

    # Словник для зберігання матчів по раундах, щоб легко їх з'єднувати
    matches_by_round = {}

    # 4. Створюємо матчі з кінця (від Фіналу до 1-го раунду)
    for current_round in range(total_rounds, 0, -1):
        matches_by_round[current_round] = []
        
        # Кількість матчів у поточному раунді (Фінал = 1, Півфінал = 2, Чвертьфінал = 4)
        num_matches_in_round = 2 ** (total_rounds - current_round) 
        
        for i in range(num_matches_in_round):
            match = Match(
                tournament=tournament,
                round_number=current_round,
                status=Match.Status.PENDING
            )
            
            # Якщо це НЕ фінал, з'єднуємо цей матч із наступним раундом
            if current_round < total_rounds:
                # Кожні 2 матчі поточного раунду ведуть до 1 матчу наступного
                next_round_matches = matches_by_round[current_round + 1]
                match.next_match = next_round_matches[i // 2]
                
            match.save()
            matches_by_round[current_round].append(match)

    # 5. Тепер розсаджуємо наші перемішані команди у матчі 1-го раунду
    round_1_matches = matches_by_round[1]
    team_index = 0
    for match in round_1_matches:
        match.team1 = teams[team_index]
        match.team2 = teams[team_index + 1]
        match.save()
        team_index += 2

    # 6. Змінюємо статус турніру на Активний
    tournament.status = Tournament.Status.ACTIVE
    tournament.save()

    return True, "Сітка успішно згенерована! Турнір розпочато."