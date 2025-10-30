from django.urls import path
from . import views

urlpatterns = [
    path("health", views.health),
    path("player/<str:name>", views.player_lookup),
]
