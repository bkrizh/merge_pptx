from django.core.paginator import Paginator
from presentation.settings import num_posts


def get_paginator(docs, request):
    """Функция описывает работу пагинации.
    Создается объект, на вход которого передают список,
    и число элементов которое требуется выводить на одну страницу.
    Выводит полученный список страниц.
    """
    paginator = Paginator(docs, num_posts)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
