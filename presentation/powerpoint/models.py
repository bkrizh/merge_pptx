from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator

User = get_user_model()


class Document(models.Model):
    author = models.ForeignKey(User, verbose_name='Автор', on_delete=models.CASCADE, related_name='documentauthor')
    file = models.FileField(verbose_name='Файл', upload_to='documents', validators=[FileExtensionValidator(allowed_extensions=['ppt', 'pptx'])])
    pub_date = models.DateTimeField(verbose_name='Время добавления', auto_now_add=True)
    description = models.CharField(verbose_name='Описание', max_length=200, blank=True, null=True)

    def __str__(self):
        return self.description if self.description else "Без описания"

    class Meta:
        verbose_name = 'Начальная презентация'
        verbose_name_plural = 'Начальные презентации'
        ordering = ['-pk']


class MainDocument(models.Model):
    author = models.ForeignKey(User, verbose_name='Автор', on_delete=models.CASCADE, related_name='mainauthor')
    file = models.FileField(verbose_name='Сформированный файл', upload_to='maindocuments', validators=[FileExtensionValidator(allowed_extensions=['ppt', 'pptx'])])
    pub_date = models.DateTimeField(verbose_name='Дата формирования', auto_now_add=True)
    description = models.CharField(verbose_name='Описание', max_length=200, blank=True, null=True)

    def __str__(self):
        return self.description if self.description else "Без описания"

    class Meta:
        verbose_name = 'Сформированная презентация'
        verbose_name_plural = 'Сформированные презентации'
        ordering = ['-pk']


class SampleDocument(models.Model):
    author = models.ForeignKey(User, verbose_name='Автор', on_delete=models.CASCADE, related_name='sampleauthor')
    file = models.FileField(verbose_name='Титульные слайды', upload_to='sampledocuments', validators=[FileExtensionValidator(allowed_extensions=['ppt', 'pptx'])])
    pub_date = models.DateTimeField(verbose_name='Время добавления', auto_now_add=True)
    description = models.CharField(verbose_name='Описание', max_length=200, blank=True, null=True)

    def __str__(self):
        return self.description if self.description else "Без описания"

    class Meta:
        verbose_name = 'Титульный шаблон презентации'
        verbose_name_plural = 'Титульные шаблоны презентации'
        ordering = ['-pk']
