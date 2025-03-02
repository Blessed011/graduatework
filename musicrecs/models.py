from django.db import models
from django.contrib.auth.models import BaseUserManager


from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, login, password, name=None):
        if not login or not password:
            raise ValueError("Логин и пароль обязательны")

        hashed_password = make_password(password)  # Хешируем пароль перед сохранением
        user = self.model(login=login, password=hashed_password, name=name)
        user.save(using=self._db)
        return user

class User(models.Model):
    id = models.AutoField(primary_key=True)
    login = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)  # Пароль хранится в хешированном виде
    name = models.CharField(max_length=255, blank=True, null=True)

    objects = UserManager()

    class Meta:
        db_table = "users"

    def set_password(self, raw_password):
        """Хеширует и сохраняет пароль"""
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """Проверяет пароль"""
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.login

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