from django.db import models

class User(models.Model):
    name = models.CharField(max_length=255)
    login = models.CharField(max_length=255, unique=True)
    password = models.TextField()

    class Meta:
        managed = False  
        db_table = 'users'

class Track(models.Model):
    track = models.TextField()
    artist = models.TextField()
    year = models.IntegerField()
    duration = models.IntegerField()
    time_signature = models.IntegerField()
    danceability = models.FloatField()
    energy = models.FloatField()
    key = models.IntegerField()
    loudness = models.FloatField()
    mode = models.IntegerField()
    speechiness = models.FloatField()
    acousticness = models.FloatField()
    instrumentalness = models.FloatField()
    liveness = models.FloatField()
    valence = models.FloatField()
    tempo = models.FloatField()
    popularity = models.IntegerField()
    genre = models.TextField()

    class Meta:
        managed = False  
        db_table = 'tracks'

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    track = models.ForeignKey(Track, on_delete=models.CASCADE)

    class Meta:
        managed = False  
        db_table = 'favorites'

class Recommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    track = models.ForeignKey(Track, on_delete=models.CASCADE)
    reason = models.TextField()

    class Meta:
        managed = False  
        db_table = 'recommendations'