"""Контроллеры для управления пользователями и платежами в приложении users."""

from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import generics, serializers, status
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import Payment, User
from users.serializers import PaymentSerializer, UserSerializer
from users.services import (
    create_stripe_price,
    create_stripe_product,
    create_stripe_session,
    retrieve_stripe_session,
)


class UserCreateAPIView(generics.CreateAPIView):
    """Эндпоинт для регистрации нового пользователя. Доступен без авторизации."""

    serializer_class = UserSerializer
    queryset = User.objects.all()
    permission_classes = (AllowAny,)


class UserListAPIView(generics.ListAPIView):
    """Эндпоинт для получения списка всех пользователей."""

    serializer_class = UserSerializer
    queryset = User.objects.all()


class UserRetrieveAPIView(generics.RetrieveAPIView):
    """Эндпоинт для получения детальной информации о пользователе."""

    serializer_class = UserSerializer
    queryset = User.objects.all()


class UserUpdateAPIView(generics.UpdateAPIView):
    """Эндпоинт для полного или частичного обновления профиля пользователя."""

    serializer_class = UserSerializer
    queryset = User.objects.all()


class UserDestroyAPIView(generics.DestroyAPIView):
    """Эндпоинт для удаления пользователя из системы."""

    serializer_class = UserSerializer
    queryset = User.objects.all()


class PaymentListAPIView(generics.ListAPIView):
    """Эндпоинт для вывода списка платежей с поддержкой фильтрации и сортировки."""

    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ('paid_course', 'paid_lesson', 'payment_method')
    ordering_fields = ('payment_date',)
    ordering = ('-payment_date',)


class PaymentCreateAPIView(generics.CreateAPIView):
    """Эндпоинт для создания платежа и генерации ссылки на оплату через Stripe."""

    serializer_class = PaymentSerializer
    queryset = Payment.objects.all()

    def perform_create(self, serializer):
        """Создает продукт, цену и сессию в Stripe, сохраняя ссылку и ID сессии в платеже."""
        payment = serializer.save(user=self.request.user)

        if payment.paid_course:
            product_name = payment.paid_course.title
        elif payment.paid_lesson:
            product_name = payment.paid_lesson.title
        else:
            product_name = 'Оплата обучения'

        product = create_stripe_product(product_name)
        price = create_stripe_price(payment.payment_amount, product['id'])
        session = create_stripe_session(price['id'])

        payment.session_id = session['id']
        payment.link = session['url']
        payment.status = session.get('payment_status', 'unpaid')
        payment.save()


class PaymentStatusAPIView(APIView):
    """Эндпоинт для проверки актуального статуса платежной сессии в Stripe."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Проверка статуса платежа в Stripe',
        description='Обращается к Stripe Session Retrieve по ID платежа в базе данных и обновляет его статус.',
        responses={
            200: inline_serializer(
                name='PaymentStatusResponse',
                fields={
                    'payment_id': serializers.IntegerField(),
                    'session_id': serializers.CharField(),
                    'payment_status': serializers.CharField(),
                    'session_status': serializers.CharField(),
                }
            )
        }
    )
    def get(self, request, pk):
        """Возвращает обновленный статус платежа из Stripe."""
        payment = get_object_or_404(Payment, pk=pk)

        if not payment.session_id:
            return Response(
                {'error': 'Для данного платежа не создана сессия Stripe.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        session_data = retrieve_stripe_session(payment.session_id)
        payment.status = session_data.get('payment_status', payment.status)
        payment.save()

        return Response({
            'payment_id': payment.id,
            'session_id': payment.session_id,
            'payment_status': payment.status,
            'session_status': session_data.get('status'),
        })
