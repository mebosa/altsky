from django.urls import path
from . import views

urlpatterns = [
    path("health", views.health),
    path("player/<str:name>", views.player_lookup),
    path("profile/<str:uuid>", views.hypixel_profile),
    path("hypixel/profile/<str:uuid>", views.hypixel_profile),
    path("hypixel/profile/<str:uuid>/<str:profile_id>", views.hypixel_profile_summary),
]
