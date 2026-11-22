from rest_framework import serializers
from lms.models import Course, Lesson, Subscription
from lms.validators import YoutubeOnlyValidator


class LessonSerializer(serializers.ModelSerializer):
    """Сериализатор для модели урока с проверкой ссылок на сторонние ресурсы."""

    class Meta:
        model = Lesson
        fields = '__all__'
        validators = [
            YoutubeOnlyValidator(field='video_url'),
            YoutubeOnlyValidator(field='description'),
        ]


class CourseSerializer(serializers.ModelSerializer):
    """Сериализатор для модели курса с подсчетом уроков, их выводом и признаком подписки."""

    lessons_count = serializers.SerializerMethodField()
    lessons = LessonSerializer(many=True, read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ('id', 'title', 'preview', 'description', 'lessons_count', 'lessons', 'is_subscribed')
        validators = [
            YoutubeOnlyValidator(field='description'),
        ]

    def get_lessons_count(self, obj):
        """Возвращает количество уроков, привязанных к текущему курсу."""
        return obj.lessons.count()

    def get_is_subscribed(self, obj):
        """Возвращает True, если текущий авторизованный пользователь подписан на курс, иначе False."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(user=request.user, course=obj).exists()
        return False
