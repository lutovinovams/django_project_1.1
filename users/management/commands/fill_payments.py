from django.core.management.base import BaseCommand
from users.models import User, Payment
from lms.models import Course, Lesson

class Command(BaseCommand):
    help = 'Заполнение таблицы платежей тестовыми данными'

    def handle(self, *args, **options):
        # Очищаем старые платежи перед заполнением (опционально)
        Payment.objects.all().delete()

        # Получаем пользователя и курс для связывания платежей
        user = User.objects.first()
        course = Course.objects.first()
        lesson = Lesson.objects.first()

        if not user:
            self.stdout.write(self.style.ERROR('Сначала создайте суперпользователя через createsuperuser!'))
            return
        if not course:
            self.stdout.write(self.style.WARNING('В базе нет курсов. Платежи будут созданы без привязки к курсу.'))

        # Создаем тестовые платежи
        payments_data = [
            {
                "user": user,
                "paid_course": course,
                "payment_amount": 15000.00,
                "payment_method": Payment.TRANSFER
            },
            {
                "user": user,
                "paid_lesson": lesson,
                "payment_amount": 1500.00,
                "payment_method": Payment.CASH
            }
        ]

        for data in payments_data:
            Payment.objects.create(**data)

        self.stdout.write(self.style.SUCCESS('Таблица платежей успешно заполнена тестовыми данными!'))
