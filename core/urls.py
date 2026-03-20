from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("tournaments/", views.tournaments_list, name="tournaments"),
    path('tournaments/<int:pk>/', views.tournament_detail, name='tournament_detail'),
    path('friends/', views.friends_view, name='friends'),
    path('friends/add/<int:user_id>/', views.send_friend_request, name='send_friend_request'),
    path('friends/accept/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('friends/reject/<int:request_id>/', views.reject_friend_request, name='reject_friend_request'),
    path('friends/remove/<int:user_id>/', views.remove_friend, name='remove_friend'),
    path('notifications/live/', views.get_notifications, name='get_notifications'),
    path('lobby/<int:lobby_id>/players/', views.get_lobby_players, name='get_lobby_players'),
    path('search/', views.search_results, name='search'),
    path("u/<str:username>/", views.public_profile, name="public_profile"),
    path("chat/<str:username>/", views.direct_chat, name="direct_chat"),
]
