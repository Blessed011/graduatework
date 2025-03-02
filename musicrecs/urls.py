from django.urls import path
from .views import get_tracks, get_track_details, add_to_favorites, remove_from_favorites, get_favorites

urlpatterns = [
    path('tracks/', get_tracks, name='get_tracks'),
    path('tracks/<int:track_id>/', get_track_details, name='get_track_details'),
    path('favorites/add/', add_to_favorites, name='add_to_favorites'),
    path('favorites/remove/', remove_from_favorites, name='remove_from_favorites'),
    path('favorites/<int:user_id>/', get_favorites, name='get_favorites'),
]
