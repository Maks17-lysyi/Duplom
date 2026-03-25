import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from lobbies.models import Game, Lobby, Tournament
from users.models import DirectMessage, FriendRequest, GamerProfile, Notification

User = get_user_model()


class SquadUpFullTests(TestCase):
    def setUp(self):
        """
        Налаштування тестової бази перед КОЖНИМ тестом.
        """
        self.client = Client()

        # 1. Створюємо юзерів
        self.user1 = User.objects.create_user(username="Doter", password="testpassword123")
        self.user2 = User.objects.create_user(username="S1mple", password="testpassword123")

        # 2. ❗ВИПРАВЛЕНО❗ Створюємо ігри безпечно через get_or_create
        self.cs2, _ = Game.objects.get_or_create(
            slug="cs2", defaults={"name": "Counter-Strike 2", "is_active": True, "order": 1}
        )
        self.dota2, _ = Game.objects.get_or_create(
            slug="dota2", defaults={"name": "Dota 2", "is_active": True, "order": 2}
        )

        # Оновлюємо профілі, які створилися автоматично через сигнали
        self.user1.gamer_profile.main_game = self.cs2
        self.user1.gamer_profile.cs2_faceit_lvl = 10
        self.user1.gamer_profile.cs2_faceit_elo = 3000
        self.user1.gamer_profile.save()

        # 3. Створюємо тестове лобі
        self.lobby = Lobby.objects.create(
            host=self.user1,
            game=self.cs2,
            title="Test CS2 Pro Lobby",
            status=Lobby.Status.ACTIVE,
            slots_total=5,
        )

        # 4. Створюємо тестовий турнір
        self.tournament = Tournament.objects.create(
            title="Major 2026 Championship",
            game=self.cs2,
            date_time=timezone.now() + timezone.timedelta(days=1),
            is_active=True,
        )

    # ==========================================
    # ТЕСТИ МОДЕЛЕЙ ТА ЛОГІКИ
    # ==========================================

    def test_gamer_profile_display_rank(self):
        """Перевіряємо, чи правильно працює розумний ранг"""
        self.assertIn("Faceit Lvl 10 (3000 ELO)", self.user1.gamer_profile.display_rank)

    # ==========================================
    # ТЕСТИ ГОЛОВНИХ СТОРІНОК (ДЛЯ COVERAGE 60%+)
    # ==========================================

    def test_home_view_loads_successfully(self):
        """Перевіряємо, чи вантажиться головна сторінка без помилок"""
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")

    def test_home_view_with_search(self):
        """Перевіряємо пошук лобі на головній сторінці"""
        response = self.client.get(reverse("home"), {"q": "Pro Lobby"})
        self.assertEqual(response.status_code, 200)
        # Лобі має бути в контексті
        self.assertIn(self.lobby, response.context["lobbies"])

    def test_home_view_ajax_request(self):
        """Перевіряємо AJAX запит на головній (повертає JSON)"""
        response = self.client.get(reverse("home"), HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("html", data)
        self.assertIn("pagination_html", data)

    def test_global_search_results_view(self):
        """Перевіряємо нову сторінку глобального пошуку"""
        response = self.client.get(reverse("search"), {"q": "S1mple"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "search_results.html")
        # Юзер S1mple має бути знайдений
        self.assertIn(self.user2, response.context["users"])

    def test_tournaments_list_view(self):
        """Перевіряємо сторінку турнірів"""
        response = self.client.get(reverse("tournaments"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.tournament, response.context["tournaments"])

    # ==========================================
    # ТЕСТИ КОРИСТУВАЧА ТА ДРУЗІВ
    # ==========================================

    def test_public_profile_view(self):
        """Перевіряємо завантаження публічного профілю іншого гравця"""
        self.client.login(username="S1mple", password="testpassword123")
        response = self.client.get(reverse("public_profile", args=[self.user1.username]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/public_profile.html")
        self.assertEqual(response.context["target_user"], self.user1)

    def test_friends_view_loads(self):
        """Перевіряємо завантаження сторінки друзів (потребує логіну)"""
        self.client.login(username="Doter", password="testpassword123")
        response = self.client.get(reverse("friends"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/friends.html")

    def test_send_friend_request(self):
        """Перевіряємо логіку відправки запиту в друзі"""
        self.client.login(username="Doter", password="testpassword123")

        # Імітуємо клік по кнопці "Add Friend"
        url = reverse("send_friend_request", args=[self.user2.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertTrue(
            FriendRequest.objects.filter(from_user=self.user1, to_user=self.user2).exists()
        )

    def test_invite_to_lobby_creates_notification(self):
        """Перевіряємо, чи створюється сповіщення при інвайті в лобі"""
        self.client.login(username="Doter", password="testpassword123")

        # Імітуємо запрошення
        url = reverse("lobby_invite_friend", args=[self.lobby.id, self.user2.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        # Перевіряємо, чи S1mple отримав сповіщення
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.user2, notification_type="lobby_invite"
            ).exists()
        )

    def test_get_notifications_htmx(self):
        """Перевіряємо отримання сповіщень через HTMX"""
        self.client.login(username="Doter", password="testpassword123")
        response = self.client.get(reverse("get_notifications"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "lobbies/partials/notifications.html")
