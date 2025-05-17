from django.contrib import admin

from .models import Document, MainDocument, SampleDocument
from django.contrib import admin


EMPTY = '-пусто-'


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'author',
        'file',
        'description',
        'pub_date',
    ]
    search_fields = [
        'author',
        'file',
        'description',
        'pub_date',
    ]
    list_per_page = 12
    empty_value_display = EMPTY


@admin.register(MainDocument)
class MainDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'author',
        'file',
        'description',
        'pub_date',
    ]
    search_fields = [
        'author',
        'file',
        'description',
        'pub_date',
    ]
    list_per_page = 12
    empty_value_display = EMPTY


@admin.register(SampleDocument)
class SampleDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'author',
        'file',
        'description',
        'pub_date',
    ]
    search_fields = [
        'author',
        'file',
        'description',
        'pub_date',
    ]
    list_per_page = 12
    empty_value_display = EMPTY
