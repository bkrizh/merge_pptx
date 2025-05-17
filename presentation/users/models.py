from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """ Модель пользователя. """

    username = models.CharField(
        verbose_name="Логин",
        max_length=150,
        unique=True
    )
    email = models.EmailField(
        verbose_name="Электронная почта",
        max_length=254
    )
    first_name = models.CharField(
        verbose_name="Имя",
        max_length=150
    )
    last_name = models.CharField(
        verbose_name="Фамилия",
        max_length=150
    )
    role = models.CharField(
        verbose_name="Роль",
        max_length=50,
        choices=[('empty', 'Нет'), ('admin', 'Администратор'), ('moder', 'Модератор')],
        default='empty'
    )

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = [
        'email',
        'first_name',
        'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-pk']
