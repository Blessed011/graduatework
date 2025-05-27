from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from .models import Track, Favorite, User, Recommendation
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.hashers import check_password, make_password
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q
import json
import logging
import re
from .recommendations import get_content_based_recommendations, get_collaborative_recommendations, save_recommendations

from .forms import TrackRequestForm
from django.conf import settings
from django.core.mail import EmailMessage


# Получение списка всех треков
def get_tracks(request):
    query = request.GET.get("q", "")
    sort_by = request.GET.get("sort_by", "name")

    tracks_list = Track.objects.filter(
        Q(track__icontains=query) | Q(artist__icontains=query)
    ).order_by("track" if sort_by == "name" else "-popularity")

    paginator = Paginator(tracks_list, 24)
    page_number = request.GET.get("page")
    tracks = paginator.get_page(page_number)

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
        next_url = request.POST.get("next", "/")

        if not user_id or not track_id:
            return JsonResponse({"error": "user_id и track_id обязательны"}, status=400)

        Favorite.objects.get_or_create(user_id=user_id, track_id=track_id)

        return redirect(next_url)

# Удаление трека из избранного
def remove_from_favorites(request):
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        track_id = request.POST.get("track_id")
        next_url = request.POST.get("next", "/")

        if not user_id or not track_id:
            return JsonResponse({"error": "user_id и track_id обязательны"}, status=400)

        Favorite.objects.filter(user_id=user_id, track_id=track_id).delete()

        return redirect(next_url)



# Получение избранных треков пользователя
def get_favorites(request, user_id):
    query = request.GET.get("q", "")
    sort_by = request.GET.get("sort_by", "name")

    # Получение избранных треков с фильтрацией и сортировкой
    favorites = Favorite.objects.filter(user_id=user_id).select_related("track")

    # Фильтрация по названию или исполнителю
    favorite_tracks = [
        fav.track
        for fav in favorites
        if query.lower() in fav.track.track.lower() or query.lower() in fav.track.artist.lower()
    ]

    # Сортировка треков
    if sort_by == "name":
        favorite_tracks.sort(key=lambda x: x.track.lower())
    elif sort_by == "popularity":
        favorite_tracks.sort(key=lambda x: x.popularity, reverse=True)

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
        
        if not re.match(r'^[a-zA-Z0-9_]+$', login):
            return render(request, "musicrecs/register.html", {"error": "Логин может содержать только латинские буквы, цифры и подчёркивания"})

        if len(password) < 2 or len(password) > 20:
            return render(request, "musicrecs/register.html", {"error": "Пароль должен быть от 2 до 20 символов"})
        
        if User.objects.filter(login=login).exists():
            return render(request, "musicrecs/register.html", {"error": "Такой пользователь уже существует"})

        hashed_password = make_password(password)
        user = User.objects.create(login=login, password=hashed_password, name=name)

        # Автоматически логиним пользователя после регистрации
        request.session["user_id"] = user.id
        request.session["user_login"] = user.login
        request.session["user_name"] = user.name

        return redirect("about")

    return render(request, "musicrecs/register.html")

# Вход пользователя
from django.contrib.auth import login as auth_login

def login(request):
    if request.method == "POST":
        login_value = request.POST.get("login")
        password = request.POST.get("password")

        if not login_value or not password:
            return render(request, "musicrecs/login.html", {"error": "Логин и пароль обязательны"})
        
        if not re.match(r'^[a-zA-Z0-9_]+$', login_value):
            return render(request, "musicrecs/login.html", {"error": "Логин может содержать только латинские буквы, цифры и подчёркивания"})

        try:
            user = User.objects.get(login=login_value)
        except User.DoesNotExist:
            return render(request, "musicrecs/login.html", {"error": "Неверный логин или пароль"})

        if not check_password(password, user.password):
            return render(request, "musicrecs/login.html", {"error": "Неверный логин или пароль"})

        # Сохранение данных в сессию
        request.session["user_id"] = user.id
        request.session["user_login"] = user.login
        request.session['user_name'] = user.name

        return redirect("about")

    return render(request, "musicrecs/login.html")
        

logger = logging.getLogger(__name__)
# Выход пользователя
@csrf_exempt
def logout(request):
    request.session.flush()  # Очистка сессии
    return redirect("login")


# # Получить рекомендации для конкретного трека
def get_track_recommendations(request, track_id):
    track = get_object_or_404(Track, id=track_id)
    recommendations_raw = get_content_based_recommendations(track_id)
    recommendations_raw.sort(key=lambda x: x['similarity'], reverse=True)
    user_id = request.session.get("user_id")

    if user_id:
        save_recommendations(user_id, recommendations_raw, source="track", track_id=track_id)
        return redirect("show_recommendations")
    else:
        recommended_tracks = []
        for rec in recommendations_raw:
            rec_track = get_object_or_404(Track, id=rec["track_id"])
            recommended_tracks.append({
                "track": rec_track,
                "reason": rec["reason"]
            })

        context = {
            "recommendations": recommended_tracks,
            "based_on_track": track
        }
        return render(request, "musicrecs/recommendations.html", context)


# Получить рекомендации на основе избранного
def get_favorites_recommendations(request, user_id):
    session_user_id = request.session.get("user_id")
    if not session_user_id or int(user_id) != session_user_id:
        return redirect("login")

    recommendations = get_collaborative_recommendations(user_id, top_n=15)
    recommendations.sort(key=lambda x: x['similarity'], reverse=True)

    if recommendations:
        save_recommendations(user_id, recommendations, source="favorites")

    return redirect("show_recommendations")

# Показать список рекомендаций
def show_recommendations(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    recommendations_raw = Recommendation.objects.filter(user_id=user_id).select_related("track")

    recommendations = []
    for rec in recommendations_raw:
        recommendations.append({
            "track": rec.track,
            "reason": rec.reason,
        })

    context = {
        "recommendations": recommendations,
    }
    return render(request, "musicrecs/recommendations.html", context)



def about(request):
    return render(request, "musicrecs/about.html")

def request_track_view(request):
    if request.method == 'POST':
        form = TrackRequestForm(request.POST, request.FILES)
        if form.is_valid():
            subject = "Запрос на добавление нового трека"
            message = (
                f"Название трека: {form.cleaned_data['track_name']}\n"
                f"Исполнитель: {form.cleaned_data['artist']}\n"
                f"Жанр: {form.cleaned_data['genre'] or 'не указан'}"
            )
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [settings.ADMIN_EMAIL]

            email = EmailMessage(subject, message, from_email, recipient_list)

            # Если файл прикреплён — добавить как вложение
            mp3_file = form.cleaned_data.get('mp3_file')
            if mp3_file:
                email.attach(mp3_file.name, mp3_file.read(), mp3_file.content_type)

            email.send()

            return render(request, 'musicrecs/track_request_sent.html')
    else:
        form = TrackRequestForm()
    return render(request, 'musicrecs/request_track.html', {'form': form})