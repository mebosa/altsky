from django.urls import path, re_path
from . import views

urlpatterns = [
    path("health", views.health),
    path("player/<str:name>", views.player_lookup),
    path("profile/<str:uuid>", views.hypixel_profile),
    path("hypixel/profile/<str:uuid>", views.hypixel_profile),
    path("hypixel/profile/<str:uuid>/<str:profile_id>", views.hypixel_profile_summary),
    path("hypixel/auctions/<str:uuid>", views.hypixel_player_auctions),
    path("og/site.png", views.site_preview_image),
    path("og/site-v2.png", views.site_preview_image_v2),
    path("og/site-v3.png", views.site_preview_image_v3),
    path("og/player/<str:name>.png", views.player_preview_image),
    path("texture/armor/<str:item_id>/<str:layer>", views.get_armor_texture_view),
    path("texture/vanilla-armor/<str:name>/<str:layer>", views.get_vanilla_armor_texture_view),
    path("textures/batch", views.get_item_textures_batch),
    re_path(r"^static/(?P<path>.*)$", views.serve_furfsky_texture),
    re_path(r"^vanilla/(?P<path>.*)$", views.serve_vanilla_texture),
]
