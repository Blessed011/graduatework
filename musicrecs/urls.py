from django.urls import path
from .views import *

urlpatterns = [
    path('tracks/', get_tracks, name='get_tracks'),
    path('tracks/<int:track_id>/', get_track_details, name='get_track_details'),
    path('favorites/add/', add_to_favorites, name='add_to_favorites'),
    path('favorites/remove/', remove_from_favorites, name='remove_from_favorites'),
    path('favorites/<int:user_id>/', get_favorites, name='get_favorites'),
    path("register/", register, name="register"),
    path("login/", login, name="login"),
    path("logout/", logout, name="logout"),
]
