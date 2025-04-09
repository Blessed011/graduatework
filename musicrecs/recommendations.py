import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from .models import Track, Favorite, Recommendation


# Получение данных из таблицы треков в DataFrame
def load_tracks_data():
    tracks = Track.objects.all().values()
    df = pd.DataFrame(list(tracks))
    return df




# Функция для извлечения признаков для content-based фильтрации
def extract_features(df):
    feature_cols = ["danceability", "energy", "valence", "tempo", "popularity"]
    df["features"] = df[feature_cols].apply(lambda row: row.tolist(), axis=1)
    return df


# Content-based рекомендации для конкретного трека
def get_content_based_recommendations(track_id, top_n=5):
    df = load_tracks_data()
    df = extract_features(df)

    # Получение данных о выбранном треке
    selected_track = df[df["id"] == track_id]

    if selected_track.empty:
        return []

    # Вычисляем сходство по косинусному расстоянию
    similarity = cosine_similarity(df["features"].tolist(), selected_track["features"].tolist())
    df["similarity"] = similarity[:, 0]

    # Исключаем сам трек и выбираем top_n похожих треков
    recommended_tracks = (
        df[df["id"] != track_id].sort_values(by="similarity", ascending=False).head(top_n)
    )

    # Формируем рекомендации и объяснения
    recommendations = []
    for _, row in recommended_tracks.iterrows():
        reason = f"Похож на трек '{selected_track.iloc[0]['track']}' по характеристикам."
        recommendations.append(
            {"track_id": row["id"], "reason": reason}
        )

    return recommendations


# Коллаборативные рекомендации на основе избранного
def get_collaborative_recommendations(user_id, top_n=5):
    favorites = Favorite.objects.filter(user_id=user_id).values_list("track_id", flat=True)

    if not favorites:
        return []

    df = load_tracks_data()
    df = extract_features(df)

    # Фильтруем избранные треки
    favorite_tracks_df = df[df["id"].isin(favorites)]

    # Считаем средний профиль пользователя по избранному
    user_profile = favorite_tracks_df["features"].tolist()
    user_profile_avg = pd.DataFrame(user_profile).mean().tolist()

    # Вычисляем сходство по среднему профилю
    similarity = cosine_similarity(df["features"].tolist(), [user_profile_avg])
    df["similarity"] = similarity[:, 0]

    # Исключаем уже добавленные в избранное треки и выбираем top_n рекомендаций
    recommended_tracks = (
        df[~df["id"].isin(favorites)].sort_values(by="similarity", ascending=False).head(top_n)
    )

    # Формируем рекомендации и объяснения
    recommendations = []
    for _, row in recommended_tracks.iterrows():
        reason = f"Похож на ваши избранные треки."
        recommendations.append(
            {"track_id": row["id"], "reason": reason}
        )

    return recommendations


# Сохранение рекомендаций в таблицу recommendations
def save_recommendations(user_id, recommendations):
    Recommendation.objects.filter(user_id=user_id).delete()  # Очистка предыдущих рекомендаций
    for rec in recommendations:
        Recommendation.objects.create(
            user_id=user_id,
            track_id=rec["track_id"],
            reason=rec["reason"]
        )
