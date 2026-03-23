from django.urls import path

from . import views

urlpatterns = [
    path("create/", views.lobby_create, name="lobby_create"),
    path("<int:lobby_id>/", views.lobby_detail, name="lobby_detail"),
    path("<int:lobby_id>/join/", views.lobby_join, name="lobby_join"),
    path("<int:lobby_id>/leave/", views.lobby_leave, name="lobby_leave"),
    path("<int:lobby_id>/end/", views.lobby_end, name="lobby_end"),
    path("<int:lobby_id>/chat/messages/", views.lobby_chat_messages, name="lobby_chat_messages"),
    path("<int:lobby_id>/chat/send/", views.lobby_chat_send, name="lobby_chat_send"),
    path("<int:lobby_id>/invite/<int:friend_id>/", views.invite_friend, name="lobby_invite_friend"),
    path(
        "invite-accept/<int:notification_id>/",
        views.accept_lobby_invite,
        name="accept_lobby_invite",
    ),
    path(
        "invite-reject/<int:notification_id>/",
        views.reject_lobby_invite,
        name="reject_lobby_invite",
    ),
]
