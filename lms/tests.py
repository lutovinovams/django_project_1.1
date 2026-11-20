from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from lms.models import Course, Lesson, Subscription
from users.models import User


class LessonTestCase(APITestCase):
    """Тестирование CRUD-операций для уроков и разграничения прав доступа."""

    def setUp(self):
        """Подготовка тестовых данных: пользователи с разными ролями, курс и урок."""
        self.user = User.objects.create(email='user@test.ru')
        self.user.set_password('TestPass123')
        self.user.save()

        self.moder = User.objects.create(email='moder@test.ru')
        self.moder.set_password('TestPass123')
        self.moder.save()

        self.moder_group = Group.objects.create(name='moders')
        self.moder.groups.add(self.moder_group)

        self.course = Course.objects.create(
            title='Тестовый курс',
            description='Описание тестового курса'
        )
        self.lesson = Lesson.objects.create(
            title='Тестовый урок',
            description='Описание урока',
            video_url='https://youtube.com',
            course=self.course
        )

    def test_lesson_list_authenticated(self):
        """Проверка получения списка уроков авторизованным пользователем."""
        self.client.force_authenticate(user=self.user)
        url = reverse('lms:lesson-list')
        response = self.client.get(url)
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['title'], self.lesson.title)

    def test_lesson_list_unauthenticated(self):
        """Проверка запрета доступа к списку уроков для неавторизованного пользователя."""
        url = reverse('lms:lesson-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_lesson_retrieve(self):
        """Проверка получения детальной информации об уроке."""
        self.client.force_authenticate(user=self.user)
        url = reverse('lms:lesson-get', args=(self.lesson.pk,))
        response = self.client.get(url)
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data['title'], self.lesson.title)

    def test_lesson_create_by_user(self):
        """Проверка успешного создания урока обычным пользователем с валидной ссылкой."""
        self.client.force_authenticate(user=self.user)
        url = reverse('lms:lesson-create')
        payload = {
            'title': 'Новый урок по Python',
            'description': 'Полезный материал',
            'video_url': 'https://youtube.com',
            'course': self.course.pk
        }
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lesson.objects.count(), 2)

    def test_lesson_create_invalid_url(self):
        """Проверка блокировки создания урока со ссылкой на сторонний ресурс."""
        self.client.force_authenticate(user=self.user)
        url = reverse('lms:lesson-create')
        payload = {
            'title': 'Урок с плохой ссылкой',
            'video_url': 'https://rutube.ru',
            'course': self.course.pk
        }
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Lesson.objects.count(), 1)

    def test_lesson_create_by_moder_forbidden(self):
        """Проверка запрета создания урока пользователем из группы модераторов."""
        self.client.force_authenticate(user=self.moder)
        url = reverse('lms:lesson-create')
        payload = {
            'title': 'Урок от модератора',
            'video_url': 'https://youtube.com',
            'course': self.course.pk
        }
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Lesson.objects.count(), 1)

    def test_lesson_update_by_moder(self):
        """Проверка возможности редактирования любого урока модератором."""
        self.client.force_authenticate(user=self.moder)
        url = reverse('lms:lesson-update', args=(self.lesson.pk,))
        payload = {'title': 'Обновленное модератором название'}
        response = self.client.patch(url, payload)
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data['title'], 'Обновленное модератором название')

    def test_lesson_delete_by_moder_forbidden(self):
        """Проверка запрета удаления урока модератором."""
        self.client.force_authenticate(user=self.moder)
        url = reverse('lms:lesson-delete', args=(self.lesson.pk,))
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Lesson.objects.count(), 1)

    def test_lesson_delete_by_user(self):
        """Проверка успешного удаления урока обычным пользователем."""
        self.client.force_authenticate(user=self.user)
        url = reverse('lms:lesson-delete', args=(self.lesson.pk,))
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Lesson.objects.count(), 0)


class SubscriptionTestCase(APITestCase):
    """Тестирование функционала подписки на обновления курса."""

    def setUp(self):
        """Подготовка пользователя и курса для проверки подписки."""
        self.user = User.objects.create(email='sub_user@test.ru')
        self.user.set_password('TestPass123')
        self.user.save()

        self.course = Course.objects.create(
            title='Курс для подписки',
            description='Описание курса'
        )
        self.url = reverse('lms:subscription')

    def test_subscription_toggle(self):
        """Проверка добавления и удаления подписки при повторных POST-запросах."""
        self.client.force_authenticate(user=self.user)

        response_add = self.client.post(self.url, {'course_id': self.course.pk})
        self.assertEqual(response_add.status_code, status.HTTP_200_OK)
        self.assertEqual(response_add.json(), {'message': 'подписка добавлена'})
        self.assertTrue(Subscription.objects.filter(user=self.user, course=self.course).exists())

        course_url = reverse('lms:courses-detail', args=(self.course.pk,))
        course_response = self.client.get(course_url)
        self.assertTrue(course_response.json()['is_subscribed'])

        response_remove = self.client.post(self.url, {'course_id': self.course.pk})
        self.assertEqual(response_remove.status_code, status.HTTP_200_OK)
        self.assertEqual(response_remove.json(), {'message': 'подписка удалена'})
        self.assertFalse(Subscription.objects.filter(user=self.user, course=self.course).exists())

    def test_subscription_unauthenticated(self):
        """Проверка запрета управления подпиской без авторизации."""
        response = self.client.post(self.url, {'course_id': self.course.pk})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
