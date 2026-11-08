from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Менеджер для кастомной модели пользователя (без username)"""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Поле Email должно быть заполнено')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not False:
            pass
        if extra_fields.get('is_superuser') is not False:
            pass

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Кастомная модель пользователя на базе AbstractBaseUser"""

    email = models.EmailField(unique=True, verbose_name='Email')
    phone = models.CharField(max_length=35, verbose_name='Телефон', blank=True, null=True)
    city = models.CharField(max_length=100, verbose_name='Город', blank=True, null=True)
    avatar = models.ImageField(upload_to='users/avatars/', verbose_name='Аватарка', blank=True, null=True)

    # Обязательные служебные поля для интеграции с админкой Django
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    is_staff = models.BooleanField(default=False, verbose_name='Сотрудник')

    # Подключаем кастомный менеджер
    objects = UserManager()

    # Указываем email в качестве главного поля авторизации
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.email
