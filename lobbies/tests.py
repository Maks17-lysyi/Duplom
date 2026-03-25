from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from lobbies.models import Lobby, Game

User = get_user_model()

class LobbiesViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Створюємо юзерів
        self.host_user = User.objects.create_user(username='HostUser', password='testpassword123')
        self.join_user = User.objects.create_user(username='JoinUser', password='testpassword123')
        
        # Створюємо гру
        self.game, _ = Game.objects.get_or_create(slug='cs2', defaults={'name': 'CS2', 'is_active': True, 'order': 1})
        
        # Створюємо лобі
        self.lobby = Lobby.objects.create(
            host=self.host_user,
            game=self.game,
            title="Test CS2 Lobby",
            slots_total=5,
            status=Lobby.Status.ACTIVE
        )

    def test_lobby_detail_view(self):
        """Перевірка сторінки конкретного лобі"""
        self.client.login(username='JoinUser', password='testpassword123')
        response = self.client.get(reverse('lobby_detail', args=[self.lobby.id]))
        self.assertEqual(response.status_code, 200)

    def test_lobby_create_view_get(self):
        """Перевірка відкриття форми створення лобі"""
        self.client.login(username='HostUser', password='testpassword123')
        response = self.client.get(reverse('lobby_create'))
        self.assertEqual(response.status_code, 200)

    def test_lobby_join_and_leave(self):
        """Перевірка, чи працює кнопка Join та Leave"""
        self.client.login(username='JoinUser', password='testpassword123')
        
        # Юзер приєднується
        response_join = self.client.post(reverse('lobby_join', args=[self.lobby.id]))
        self.assertEqual(response_join.status_code, 302) # Redirect після успішного входу
        self.assertTrue(self.lobby.participants.filter(user=self.join_user).exists())

        # Юзер виходить
        response_leave = self.client.post(reverse('lobby_leave', args=[self.lobby.id]))
        self.assertEqual(response_leave.status_code, 302)
        self.assertFalse(self.lobby.participants.filter(user=self.join_user).exists())