from django.urls import path

from . import views

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("me/", views.profile_view, name="profile"),
    path("me/edit/", views.profile_edit, name="profile_edit"),
    path('notifications/read/<int:notif_id>/', views.read_notification, name='read_notification'),
    path('notifications/read/<int:notif_id>/', views.read_notification, name='read_notification'),
]
