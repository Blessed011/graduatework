import pandas as pd
import os
import joblib
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
from .models import Track, Favorite, Recommendation

# Путь к файлу с моделью
MODEL_PATH = "C:\\Users\\5\Desktop\\graduate\\musicrecs\\rec_model\\hybrid_model.pkl"

# Признаки, используемые в модели
FEATURE_COLS = ["danceability", "energy", "valence", "tempo", "popularity", "instrumentalness", "acousticness"]

FEATURE_NAME_MAP = {
    "danceability": "танцевальность",
    "energy": "энергичность",
    "valence": "валентность",
    "tempo": "темп",
    "popularity": "популярность",
    "instrumentalness": "инструментальность",
    "acousticness": "акустичность"
}

# Загрузка треков из базы данных
def load_tracks_data():
    tracks = Track.objects.all().values()
    df = pd.DataFrame(list(tracks))
    return df

# Извлечение и нормализация признаков
def extract_and_save_features(df):
    scaler = StandardScaler()
    df["features_raw"] = df[FEATURE_COLS].apply(lambda row: row.tolist(), axis=1)
    features_scaled = scaler.fit_transform(df[FEATURE_COLS])
    df["features"] = list(features_scaled)

    joblib.dump({
        "df": df,
        "scaler": scaler
    }, MODEL_PATH)

    return df

# Загрузка модели из файла
def load_model_features():
    if not os.path.exists(MODEL_PATH):
        df = load_tracks_data()
        return extract_and_save_features(df)
    model = joblib.load(MODEL_PATH)
    return model["df"]

# Content-based рекомендации
def get_content_based_recommendations(track_id, top_n=15):
    df = load_model_features()

    selected_track = df[df["id"] == track_id]
    if selected_track.empty:
        return []

    similarity = cosine_similarity(df["features"].tolist(), selected_track["features"].tolist())
    df["similarity"] = similarity[:, 0]

    recommended = df[df["id"] != track_id].sort_values(by="similarity", ascending=False).head(top_n)

    recommendations = []
    for _, row in recommended.iterrows():
        reason = generate_reason(selected_track.iloc[0], row)
        recommendations.append({
            "track_id": row["id"],
            "reason": reason,
            "similarity": row["similarity"]
        })

    return recommendations

# Collaborative рекомендации
def get_collaborative_recommendations(user_id, top_n=15):
    favorites_ids = Favorite.objects.filter(user_id=user_id).values_list("track_id", flat=True)
    if not favorites_ids:
        return []

    df = load_model_features()
    fav_df = df[df["id"].isin(favorites_ids)]

    if fav_df.empty:
        return []

    user_profile_avg = pd.DataFrame(fav_df["features"].tolist()).mean().tolist()
    similarity = cosine_similarity(df["features"].tolist(), [user_profile_avg])
    df["similarity"] = similarity[:, 0]

    recommended = df[~df["id"].isin(favorites_ids)].sort_values(by="similarity", ascending=False).head(top_n)

    recommendations = []
    for _, row in recommended.iterrows():
        reason = generate_reason_from_user_profile(user_profile_avg, row)
        recommendations.append({
            "track_id": row["id"],
            "reason": reason,
            "similarity": row["similarity"]
        })

    return recommendations

# Генерация причины для рекомендации на основе другого трека
def generate_reason(base_track, similar_track):
    reasons = []
    for col in FEATURE_COLS:
        diff = abs(base_track[col] - similar_track[col])
        if diff < 0.1:
            reasons.append(FEATURE_NAME_MAP.get(col, col))
    if reasons:
        reason_str = ", ".join(reasons)
        return f"Похож на трек '{base_track['track']}' по признакам: {reason_str}."
    else:
        return f"Похож на трек '{base_track['track']}' по общим характеристикам."


# Генерация причины на основе схожести со средним профилем пользователя
def generate_reason_from_user_profile(profile_avg, track_row):
    reasons = []
    for i, col in enumerate(FEATURE_COLS):
        diff = abs(profile_avg[i] - track_row[col])
        if diff < 0.1:
            reasons.append(FEATURE_NAME_MAP.get(col, col))
    if reasons:
        reason_str = ", ".join(reasons)
        return f"Похож на ваши избранные треки по признакам: {reason_str}."
    else:
        return "Похож на ваши избранные треки по общим характеристикам."

# Сохранение рекомендаций
def save_recommendations(user_id, recommendations, source="track", track_id=None):
    Recommendation.objects.filter(user_id=user_id).delete()
    for rec in recommendations:
        Recommendation.objects.create(
            user_id=user_id,
            track_id=rec["track_id"],
            reason=rec["reason"]
        )

def print_similarity_for_track(track_id):
    df = load_model_features()
    track_row = df[df["id"] == track_id]
    if track_row.empty:
        print("Трек не найден.")
        return

    track_name = track_row.iloc[0]["track"]
    similarities = cosine_similarity(df["features"].tolist(), track_row["features"].tolist()).flatten()

    sim_df = pd.DataFrame({
        "track": df["track"],
        "similarity": similarities
    }).sort_values(by="similarity", ascending=False)

    print(f"\nСходства треков с треком '{track_name}':")
    print(sim_df.head(16).round(4))





    # Для матрицы косинусного сходства:

    # from musicrecs import recommendations
    # recommendations.print_similarity_for_track(track_id=1)



    # Для изменения состава ключевых характеристик:

    # from musicrecs.recommendations import load_tracks_data, extract_and_save_features
    # df = load_tracks_data()
    # extract_and_save_features(df)
