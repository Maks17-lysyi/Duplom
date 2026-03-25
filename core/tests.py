from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from users.models import GamerProfile, FriendRequest, Notification, DirectMessage
from lobbies.models import Game

User = get_user_model()

class SquadUpUsersTests(TestCase):
    def setUp(self):
        """
        Цей метод запускається ПЕРЕД кожним тестом. 
        Тут ми створюємо тестову базу (юзерів, ігри).
        """
        self.client = Client()
        
        # Створюємо двох гравців
        self.user1 = User.objects.create_user(username='Doter', password='testpassword123')
        self.user2 = User.objects.create_user(username='S1mple', password='testpassword123')
        
        # Створюємо гру для тестів
        self.cs2 = Game.objects.create(name='Counter-Strike 2', slug='cs2', is_active=True, order=1)

    def test_gamer_profile_display_rank(self):
        """
        Тестуємо нашу розумну властивість display_rank (чи правильно вона клеїть Lvl та ELO)
        """
        profile = self.user1.gamer_profile
        profile.main_game = self.cs2
        profile.cs2_faceit_lvl = 10
        profile.cs2_faceit_elo = 3000
        profile.save()

        # Перевіряємо, чи текст формується правильно
        self.assertIn('Faceit Lvl 10 (3000 ELO)', profile.display_rank)

    def test_send_friend_request(self):
        """
        Тестуємо відправку запиту в друзі
        """
        self.client.login(username='Doter', password='testpassword123')
        
        # Імітуємо клік по кнопці "Add Friend"
        url = reverse('send_friend_request', args=[self.user2.id])
        response = self.client.get(url)
        
        # Перевіряємо, чи перекинуло нас назад (redirect)
        self.assertEqual(response.status_code, 302)
        
        # Перевіряємо, чи з'явився запис у базі даних
        request_exists = FriendRequest.objects.filter(from_user=self.user1, to_user=self.user2, status='pending').exists()
        self.assertTrue(request_exists)

    def test_accept_friend_request(self):
        """
        Тестуємо прийняття запиту та створення сповіщень
        """
        # Створюємо запит вручну
        freq = FriendRequest.objects.create(from_user=self.user1, to_user=self.user2, status='pending')
        
        # Заходимо за другого юзера і приймаємо запит
        self.client.login(username='S1mple', password='testpassword123')
        url = reverse('accept_friend_request', args=[freq.id])
        self.client.get(url)
        
        # 1. Перевіряємо, чи стали вони друзями
        is_friend = self.user2.gamer_profile.friends.filter(id=self.user1.gamer_profile.id).exists()
        self.assertTrue(is_friend)
        
        # 2. Перевіряємо, чи змінився статус запиту
        freq.refresh_from_db()
        self.assertEqual(freq.status, 'accepted')
        
        # 3. Перевіряємо, чи відправилось сповіщення (Notification)
        notification_exists = Notification.objects.filter(recipient=self.user1, notification_type='system').exists()
        self.assertTrue(notification_exists)

    def test_direct_message_creation(self):
        """
        Тестуємо відправку повідомлення в чаті
        """
        # Спочатку робимо їх друзями
        self.user1.gamer_profile.friends.add(self.user2.gamer_profile)
        
        self.client.login(username='Doter', password='testpassword123')
        url = reverse('direct_chat', args=[self.user2.username])
        
        # Відправляємо POST запит з текстом повідомлення
        response = self.client.post(url, {'content': 'Gl hf bro!'})
        
        # Перевіряємо, чи повідомлення збереглось у базі
        msg = DirectMessage.objects.filter(sender=self.user1, receiver=self.user2).first()
        self.assertIsNotNone(msg)
        self.assertEqual(msg.content, 'Gl hf bro!')