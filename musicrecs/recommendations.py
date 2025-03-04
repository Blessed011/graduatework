import pandas as pd
import psycopg2
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))  # Добавляем текущую директорию
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))  # Добавляем корень проекта

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webapp.settings")
django.setup()

from django.conf import settings

def get_db_connection():
    return psycopg2.connect(
        dbname=settings.DATABASES['default']['NAME'],
        user=settings.DATABASES['default']['USER'],
        password=settings.DATABASES['default']['PASSWORD'],
        host=settings.DATABASES['default']['HOST'],
        port=settings.DATABASES['default']['PORT']
    )

def get_favorite_tracks(user_id):
    conn = get_db_connection()
    query = """
        SELECT t.* FROM tracks t
        JOIN favorites f ON t.id = f.track_id
        WHERE f.user_id = %s
    """
    df = pd.read_sql(query, conn, params=[user_id])
    conn.close()
    return df

def generate_recommendations(user_id, top_n=5):
    fav_tracks = get_favorite_tracks(user_id)
    if fav_tracks.empty:
        return []

    conn = get_db_connection()
    query = "SELECT * FROM tracks"
    df_all_tracks = pd.read_sql(query, conn)
    conn.close()

    feature_columns = ["danceability", "energy", "tempo", "valence", "mode", "liveness", "speechiness", "loudness"]
    recommended_tracks = set()

    for _, fav_track in fav_tracks.iterrows():
        fav_features = fav_track[feature_columns].values.reshape(1, -1)

        similarity_scores = cosine_similarity(fav_features, df_all_tracks[feature_columns].values)[0]
        df_all_tracks["similarity"] = similarity_scores

        similar_tracks = df_all_tracks.nlargest(top_n, "similarity")["track"].tolist()
        recommended_tracks.update(similar_tracks)

        if len(recommended_tracks) >= top_n:
            break

    return list(recommended_tracks)[:top_n]

def get_track_recommendations(track_name, top_n=10):
    conn = get_db_connection()
    query = "SELECT * FROM tracks WHERE track = %s"
    df_track = pd.read_sql(query, conn, params=[track_name])
    
    if df_track.empty:
        print(f"Трек '{track_name}' не найден в базе данных.")
        return []
    
    track_data = df_track.iloc[0]
    query = "SELECT * FROM tracks WHERE track != %s"
    df_all_tracks = pd.read_sql(query, conn, params=[track_name])
    
    feature_columns = ["danceability", "energy", "tempo", "valence", "liveness", "instrumentalness", "speechiness", "loudness", "acousticness"]
    similarity_scores = cosine_similarity(
        [track_data[feature_columns].values], 
        df_all_tracks[feature_columns].values
    )
    
    df_all_tracks["similarity"] = similarity_scores[0]
    content_recommendations = df_all_tracks.nlargest(top_n, "similarity")["track"].tolist()
    
    query = """
        SELECT DISTINCT t.track 
        FROM favorites f
        JOIN favorites f2 ON f.user_id = f2.user_id
        JOIN tracks t ON f2.track_id = t.id
        WHERE f.track_id = (SELECT id FROM tracks WHERE track = %s)
        AND f2.track_id != f.track_id
    """
    collab_recommendations = pd.read_sql(query, conn, params=[track_name])["track"].tolist()
    conn.close()
    
    recommendations = list(set(content_recommendations + collab_recommendations))[:top_n]
    return recommendations

############# Оценка релевантности #############

def precision_at_k(recommended, relevant, k):
    recommended = recommended[:k]
    return len(set(recommended) & set(relevant)) / k

def recall_at_k(recommended, relevant, k):
    return len(set(recommended) & set(relevant)) / len(relevant) if relevant else 0

def average_precision(recommended, relevant, k):
    score = 0.0
    num_hits = 0
    for i, rec in enumerate(recommended[:k]):
        if rec in relevant:
            num_hits += 1
            score += num_hits / (i + 1)
    return score / min(len(relevant), k) if relevant else 0

def mean_average_precision(recommended, relevant, k=10):
    return average_precision(recommended, relevant, k)

def ndcg_at_k(recommended, relevant, k):
    def dcg(scores):
        return sum((2**s - 1) / np.log2(i + 2) for i, s in enumerate(scores))
    
    relevance_scores = [1 if rec in relevant else 0 for rec in recommended[:k]]
    ideal_relevance = sorted(relevance_scores, reverse=True)
    
    return dcg(relevance_scores) / dcg(ideal_relevance) if dcg(ideal_relevance) > 0 else 0

def evaluate_recommendations(user_id, k=5):
    recommended_tracks = generate_recommendations(user_id)

    conn = get_db_connection()
    query = "SELECT t.track FROM tracks t JOIN favorites f ON t.id = f.track_id WHERE f.user_id = %s"
    relevant_tracks = pd.read_sql(query, conn, params=[user_id])["track"].tolist()
    conn.close()

    print(f"Recommended: {recommended_tracks}")
    print(f"Relevant: {relevant_tracks}")

    if not recommended_tracks:
        print("Нет рекомендаций, метрики не считаем.")
        return
    if not relevant_tracks:
        print("Нет избранных треков, нечего сравнивать.")
        return

    print("Precision@k:", precision_at_k(recommended_tracks, relevant_tracks, k))
    print("Recall@k:", recall_at_k(recommended_tracks, relevant_tracks, k))
    print("MAP:", mean_average_precision(recommended_tracks, relevant_tracks, k))
    print("NDCG@k:", ndcg_at_k(recommended_tracks, relevant_tracks, k))

if __name__ == "__main__":
    user_id = 4
    print("Рекомендации на основе избранных треков:")
    print(generate_recommendations(user_id))
    
    track_name = "Shape of You"  
    print("Рекомендации на основе одного трека:")
    print(get_track_recommendations(track_name))

    evaluate_recommendations(user_id)