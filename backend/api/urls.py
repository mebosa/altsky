from django.urls import path, re_path
from . import views

urlpatterns = [
    path("health", views.health),
    path("bazaar/flips", views.bazaar_flips),
    path("bazaar/history", views.bazaar_history),
    path("bazaar/allocate", views.bazaar_allocate),
    path("auction/flips", views.auction_flips),
    path("auction/search", views.auction_search),
    path("auction/item/<str:item_id>", views.auction_item_details),
    path("player/<str:name>", views.player_lookup),
    path("profile/<str:uuid>", views.hypixel_profile),
    path("hypixel/profile/<str:uuid>", views.hypixel_profile),
    path("hypixel/profile/<str:uuid>/<str:profile_id>", views.hypixel_profile_summary),
    # New: Name-based profile summary - single call instead of player + profile
    path("hypixel/profile-by-name/<str:name>/<str:profile_id>", views.hypixel_profile_summary_by_name),
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
