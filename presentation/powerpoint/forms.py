from django import forms
from django.core.exceptions import ValidationError
import os
from .models import Document, MainDocument, SampleDocument
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from . import models
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

EMPTY = '-пусто-'


class DocumentAddForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['file', 'description']

    def clean_file(self):
        file_field = self.cleaned_data.get('file')
        if not file_field:
            raise ValidationError("Поле document не должно быть пустым.")
        ext = os.path.splitext(file_field.name)[1]  # Получаем расширение файла
        if ext.lower() != '.pptx':
            raise ValidationError('Допустимы только файлы в формате PPTX.')
        return file_field


class MergePresentationForm(forms.ModelForm):
    presentations = forms.ModelMultipleChoiceField(
        queryset=Document.objects.all(),
        widget=forms.CheckboxSelectMultiple,  # Изменение виджета на CheckboxSelectMultiple для чекбоксов
        label='Презентации для формирования'
    )
    sample_start = forms.ModelMultipleChoiceField(
        queryset=SampleDocument.objects.filter(id=1),
        widget=forms.CheckboxSelectMultiple,
        label='Титульный слайд',
        required=False
    )
    sample_end = forms.ModelMultipleChoiceField(
        queryset=SampleDocument.objects.filter(id=2),
        widget=forms.CheckboxSelectMultiple,
        label='Конечный слайд',
        required=False
    )
    description = forms.CharField(label='Описание', widget=forms.TextInput(attrs={'class': 'form-control'}), required=False)

    class Meta:
        model = MainDocument
        fields = ['presentations', 'description']


class SampleEditForm(forms.ModelForm):
    class Meta:
        model = SampleDocument
        fields = ['file', 'description']

    def clean_file(self):
        file_field = self.cleaned_data.get('file')
        if not file_field:
            raise ValidationError("Поле document не должно быть пустым.")
        ext = os.path.splitext(file_field.name)[1]  # Получаем расширение файла
        if ext.lower() != '.pptx':
            raise ValidationError('Допустимы только файлы в формате PPT или PPTX.')
        return file_field


class MyUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = models.User
        fields = '__all__'


class MyUserAdmin(UserAdmin):
    form = MyUserChangeForm
    add_form = UserCreationForm  # Добавляем форму создания пользователя
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'role'),
        }),
    )

    # Поля, которые отображаются в профиле пользователя
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    list_display = [
        'id',
        'username',
        'first_name',
        'last_name',
        'email',
        'role'
    ]
    search_fields = ['id', 'username', 'email']
    list_filter = ['is_superuser', 'is_active', 'groups', 'role']
    list_per_page = 12
    empty_value_display = EMPTY


admin.site.register(models.User, MyUserAdmin)
