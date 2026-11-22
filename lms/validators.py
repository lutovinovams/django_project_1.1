import re
from urllib.parse import urlparse
from rest_framework.serializers import ValidationError


class YoutubeOnlyValidator:
    """Валидатор для проверки отсутствия ссылок на сторонние ресурсы, кроме youtube.com."""

    def __init__(self, field):
        self.field = field

    def __call__(self, value):
        """Проверяет переданное значение поля на наличие запрещенных URL-адресов."""
        text = value.get(self.field)
        if not text:
            return

        urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', str(text))

        for url in urls:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            domain = urlparse(url).netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]

            if domain not in ('youtube.com', 'youtu.be'):
                raise ValidationError(
                    f'Поле "{self.field}" содержит ссылку на запрещенный ресурс ({domain}). '
                    'Разрешены только ссылки на youtube.com.'
                )
