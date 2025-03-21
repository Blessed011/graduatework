from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from .models import Track, Favorite, User
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.hashers import check_password, make_password
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
import json
import logging

# Получение списка всех треков
def get_tracks(request):
    tracks = Track.objects.order_by("id")
    favorite_track_ids = (
        Favorite.objects.filter(user_id=request.session.get("user_id")).values_list("track_id", flat=True)
        if request.session.get("user_id")
        else []
    )

    context = {
        "tracks": tracks,
        "favorite_track_ids": list(favorite_track_ids),
    }
    return render(request, "musicrecs/tracks.html", context)

# Получение подробной информации о треке
def get_track_details(request, track_id):
    track = get_object_or_404(Track, id=track_id)
    favorite_track_ids = (
        Favorite.objects.filter(user_id=request.session.get("user_id")).values_list("track_id", flat=True)
        if request.session.get("user_id")
        else []
    )

    context = {
        "track": track,
        "favorite_track_ids": list(favorite_track_ids),
    }
    return render(request, "musicrecs/track_details.html", context)

# Добавление трека в избранное
def add_to_favorites(request):
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        track_id = request.POST.get("track_id")

        if not user_id or not track_id:
            return JsonResponse({"error": "user_id и track_id обязательны"}, status=400)

        favorite, created = Favorite.objects.get_or_create(user_id=user_id, track_id=track_id)

        if created:
            return redirect(request.META.get("HTTP_REFERER", "get_tracks"))
        else:
            return redirect(request.META.get("HTTP_REFERER", "get_tracks"))

    return JsonResponse({"error": "Метод не поддерживается"}, status=405)

# Удаление трека из избранного
def remove_from_favorites(request):
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        track_id = request.POST.get("track_id")

        if not user_id or not track_id:
            return JsonResponse({"error": "user_id и track_id обязательны"}, status=400)

        try:
            favorite = Favorite.objects.get(user_id=user_id, track_id=track_id)
            favorite.delete()
            return redirect(request.META.get("HTTP_REFERER", "get_tracks"))
        except Favorite.DoesNotExist:
            return redirect(request.META.get("HTTP_REFERER", "get_tracks"))

    return JsonResponse({"error": "Метод не поддерживается"}, status=405)


# Получение избранных треков пользователя
def get_favorites(request, user_id):
    favorites = Favorite.objects.filter(user_id=user_id).select_related("track")
    favorite_tracks = [fav.track for fav in favorites]

    context = {
        "favorites": favorite_tracks,
    }
    return render(request, "musicrecs/favorites.html", context)

# Регистрация нового пользователя
def register(request):
    if request.method == "POST":
        login = request.POST.get("login")
        password = request.POST.get("password")
        name = request.POST.get("name", "")

        if not login or not password:
            return render(request, "musicrecs/register.html", {"error": "Логин и пароль обязательны"})

        if User.objects.filter(login=login).exists():
            return render(request, "musicrecs/register.html", {"error": "Такой пользователь уже существует"})

        hashed_password = make_password(password)
        user = User.objects.create(login=login, password=hashed_password, name=name)

        # Автоматически логиним пользователя после регистрации
        request.session["user_id"] = user.id
        request.session["user_login"] = user.login

        return redirect("get_tracks")

    return render(request, "musicrecs/register.html")

# Вход пользователя
from django.contrib.auth import login as auth_login

def login(request):
    if request.method == "POST":
        login_value = request.POST.get("login")
        password = request.POST.get("password")

        if not login_value or not password:
            return render(request, "musicrecs/login.html", {"error": "Логин и пароль обязательны"})

        try:
            user = User.objects.get(login=login_value)
        except User.DoesNotExist:
            return render(request, "musicrecs/login.html", {"error": "Неверный логин или пароль"})

        if not check_password(password, user.password):
            return render(request, "musicrecs/login.html", {"error": "Неверный логин или пароль"})

        # Сохранение данных в сессию
        request.session["user_id"] = user.id
        request.session["user_login"] = user.login

        return redirect("get_tracks")

    return render(request, "musicrecs/login.html")
        

logger = logging.getLogger(__name__)
# Выход пользователя
@csrf_exempt
def logout(request):
    request.session.flush()  # Очистка сессии
    return redirect("login")
