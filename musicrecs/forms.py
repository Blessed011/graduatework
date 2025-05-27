from django import forms
from django.core.exceptions import ValidationError

class TrackRequestForm(forms.Form):
    track_name = forms.CharField(label="Название трека", max_length=200)
    artist = forms.CharField(label="Исполнитель", max_length=200)
    genre = forms.CharField(label="Жанр", max_length=100, required=False)
    mp3_file = forms.FileField(label="MP3-файл", required=False)

    def clean_mp3_file(self):
        mp3_file = self.cleaned_data.get('mp3_file')
        if mp3_file:
            if not mp3_file.name.endswith('.mp3'):
                raise ValidationError('Можно загрузить только MP3-файл.')
            if mp3_file.content_type != 'audio/mpeg':
                raise ValidationError('Файл должен быть в формате audio/mpeg (MP3).')
        return mp3_file