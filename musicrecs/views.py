from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Track, Favorite, User
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.hashers import check_password
from django.views.decorators.csrf import csrf_exempt
import json
import logging

# Получение списка всех треков
def get_tracks(request):
    tracks = Track.objects.order_by("id")
    data = list(tracks.values("id", "track", "artist"))
    return JsonResponse(list(data), safe=False)

# Получение подробной информации о треке
def get_track_details(request, track_id):
    track = get_object_or_404(Track, id=track_id)
    track_data = {
        "id": track.id,
        "track": track.track,
        "artist": track.artist,
        "year": track.year,
        "duration": track.duration,
        "popularity": track.popularity,
        "genre": track.genre,
    }
    return JsonResponse(track_data)

# Добавление трека в избранное
def add_to_favorites(request):
    user_id = request.POST.get("user_id")
    track_id = request.POST.get("track_id")

    if not user_id or not track_id:
        return JsonResponse({"error": "user_id и track_id обязательны"}, status=400)

    favorite, created = Favorite.objects.get_or_create(user_id=user_id, track_id=track_id)

    if created:
        return JsonResponse({"message": "Трек добавлен в избранное"}, status=201)
    else:
        return JsonResponse({"message": "Трек уже в избранном"}, status=200)

# Удаление трека из избранного
def remove_from_favorites(request):
    if request.method == "DELETE":
        try:
            data = json.loads(request.body)
            user_id = data.get("user_id")
            track_id = data.get("track_id")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Некорректный JSON"}, status=400)

        if not user_id or not track_id:
            return JsonResponse({"error": "user_id и track_id обязательны"}, status=400)

        try:
            favorite = Favorite.objects.get(user_id=user_id, track_id=track_id)
            favorite.delete()
            return JsonResponse({"message": "Трек удалён из избранного"}, status=200)
        except Favorite.DoesNotExist:
            return JsonResponse({"error": "Трек не найден в избранном"}, status=404)

    return JsonResponse({"error": "Метод не поддерживается"}, status=405)


# Получение избранных треков пользователя
def get_favorites(request, user_id):
    favorites = Favorite.objects.filter(user_id=user_id).select_related("track")
    favorite_tracks = [
        {"id": fav.track.id, "track": fav.track.track, "artist": fav.track.artist}
        for fav in favorites
    ]
    return JsonResponse(favorite_tracks, safe=False)

# Регистрация нового пользователя
def register(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            login = data.get("login")
            password = data.get("password")
            name = data.get("name", "")

            if not login or not password:
                return JsonResponse({"error": "Логин и пароль обязательны"}, status=400)

            if User.objects.filter(login=login).exists():
                return JsonResponse({"error": "Такой пользователь уже существует"}, status=400)

            user = User.objects.create_user(login=login, password=password, name=name)
            return JsonResponse({"message": "Пользователь успешно зарегистрирован"}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Неверный формат JSON"}, status=400)

    return JsonResponse({"error": "Метод не поддерживается"}, status=405)

# Вход пользователя
def login(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            login_value = data.get("login")
            password = data.get("password")

            if not login_value or not password:
                return JsonResponse({"error": "Логин и пароль обязательны"}, status=400)

            # Ищем пользователя в БД
            try:
                user = User.objects.get(login=login_value)
            except User.DoesNotExist:
                return JsonResponse({"error": "Неверный логин или пароль"}, status=401)

            # Проверяем пароль
            if not check_password(password, user.password):  # <- проверяем хэшированный пароль
                return JsonResponse({"error": "Неверный логин или пароль"}, status=401)

            # Создаём сессию вручную
            request.session["user_id"] = user.id
            request.session["user_login"] = user.login

            return JsonResponse({"message": "Успешный вход"}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Неверный формат JSON"}, status=400)

    return JsonResponse({"error": "Метод не поддерживается"}, status=405)
        

logger = logging.getLogger(__name__)
# Выход пользователя
@csrf_exempt
def logout(request):
    if request.method == "POST":
        try:
            logout(request)  # Выход пользователя
            response = JsonResponse({"message": "Вы вышли из системы"}, status=200)
            response.delete_cookie("sessionid")  # Удаляем cookie сессии
            return response
        except Exception as e:
            logger.error(f"Ошибка при выходе: {e}")
            return JsonResponse({"error": "Ошибка на сервере"}, status=500)

    return JsonResponse({"error": "Метод не поддерживается"}, status=405)
