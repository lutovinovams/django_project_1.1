from django.shortcuts import get_object_or_404
from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from lms.models import Course, Lesson, Subscription
from lms.paginators import CustomPagination
from lms.serializers import CourseSerializer, LessonSerializer
from users.permissions import IsModer


class CourseViewSet(viewsets.ModelViewSet):
    """ViewSet для CRUD-операций над курсами с разграничением прав по action и пагинацией."""

    queryset = Course.objects.all().order_by('id')
    serializer_class = CourseSerializer
    pagination_class = CustomPagination

    def get_permissions(self):
        """Определяет права доступа в зависимости от выполняемого действия (action)."""
        if self.action == 'create':
            self.permission_classes = [~IsModer]
        elif self.action in ['update', 'partial_update', 'list', 'retrieve']:
            self.permission_classes = [IsAuthenticated]
        elif self.action == 'destroy':
            self.permission_classes = [~IsModer]
        return [permission() for permission in self.permission_classes]


class LessonListAPIView(generics.ListAPIView):
    """Контроллер для получения списка всех уроков с пагинацией."""

    queryset = Lesson.objects.all().order_by('id')
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination


class LessonCreateAPIView(generics.CreateAPIView):
    """Контроллер для создания нового урока. Запрещено для модераторов."""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, ~IsModer]


class LessonRetrieveAPIView(generics.RetrieveAPIView):
    """Контроллер для получения детальной информации об уроке."""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]


class LessonUpdateAPIView(generics.UpdateAPIView):
    """Контроллер для редактирования урока."""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]


class LessonDestroyAPIView(generics.DestroyAPIView):
    """Контроллер для удаления урока. Запрещено для модераторов."""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, ~IsModer]


class SubscriptionAPIView(APIView):
    """Эндпоинт для установки и удаления подписки пользователя на обновления курса."""

    permission_classes = [IsAuthenticated]

    def post(self, *args, **kwargs):
        """Создает подписку на курс, если её нет, или удаляет существующую."""
        user = self.request.user
        course_id = self.request.data.get('course_id')
        course_item = get_object_or_404(Course, id=course_id)

        subs_item = Subscription.objects.filter(user=user, course=course_item)

        if subs_item.exists():
            subs_item.delete()
            message = 'подписка удалена'
        else:
            Subscription.objects.create(user=user, course=course_item)
            message = 'подписка добавлена'

        return Response({'message': message})
