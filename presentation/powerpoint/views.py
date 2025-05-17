from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied, BadRequest
from .models import Document, MainDocument, SampleDocument
from .forms import DocumentAddForm, MergePresentationForm, SampleEditForm
from django.conf import settings
from django.http import FileResponse
from django.contrib import messages
import os
import uuid
import win32com.client
import pythoncom
import shutil
import threading
from django.db import transaction
from django.utils import timezone
from django.http import HttpResponse
from django.core.paginator import Paginator

# Создаем объекты блокировки и условия
powerpoint_lock = threading.Lock()
condition = threading.Condition()


def handler404(request, exception):
    """
    Обработка ошибки 404
    """
    return render(request=request, template_name='users/errors.html', status=404, context={
        'title': 'Страница не найдена: 404',
        'error_message': 'Такой страницы не существует, или она перемещена.',
    })


def handler403(request, exception):
    """
    Обработка ошибки 403
    """
    return render(request=request, template_name='users/errors.html', status=403, context={
        'title': 'Ошибка доступа: 403',
        'error_message': 'Доступ к этой странице ограничен.',
    })


def index(request):
    return render(request, 'presentations/index.html', {request.user: 'user'})


@transaction.atomic
@login_required
def sample(request):
    if request.method == 'GET':
        documents = SampleDocument.objects.all()
        paginator = Paginator(documents, 8)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context = {'user': request.user, 'documents': documents, 'page_obj': page_obj}
        messages_list = list(messages.get_messages(request))
        context['success_message'] = next((msg.message for msg in messages_list if msg.level == messages.SUCCESS), None)
        context['error_message'] = next((msg.message for msg in messages_list if msg.level == messages.ERROR), None)
        messages.get_messages(request).used = True
        return render(request, 'presentations/sample.html', context)


@transaction.atomic
@login_required
def sample_edit(request, document_id):
    document = get_object_or_404(SampleDocument, pk=document_id)
    document_path = document.file.path
    name = os.path.basename(document_path)
    if request.method == 'GET':
        form = SampleEditForm(request.FILES, instance=document)
        return render(request, 'presentations/sample_edit.html', {'form': form, 'document': document, 'name': name})
    if request.method == 'POST':
        form = SampleEditForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            document = form.save(commit=False)
            document.author = request.user
            document.pub_date = timezone.now()
            document.save()
            full_path = document.file.path
            if full_path != document_path:
                os.remove(document_path)
            success_message = "Данные документа успешно изменены."
            messages.success(request, success_message)
            return redirect('powerpoint:sample')
        else:
            error_message = "Произошла ошибка при сохранении формы.<br>Возможно, вы выбрали не тот формат документа.<br>Проверьте данные и попробуйте ввести еще раз."
            messages.error(request, error_message)
            return redirect('powerpoint:sample')


@transaction.atomic
@login_required
def sample_preview(request, document_id):
    document = get_object_or_404(SampleDocument, pk=document_id)

    slides = []

    with powerpoint_lock:
        # Захватываем блокировку powerpoint_lock и ожидаем условия
        with condition:
            # Если уже есть другой запрос на обработку, ожидаем его завершения
            while condition.wait(timeout=1):
                pass

            try:
                old_preview_folder = os.path.join(settings.MEDIA_ROOT, 'previews')
                if os.path.exists(old_preview_folder):
                    shutil.rmtree(old_preview_folder)

                # Ensure Python COM is initialized
                pythoncom.CoInitialize()

                # Initialize PowerPoint application
                powerpoint = win32com.client.Dispatch("PowerPoint.Application")
                powerpoint.Visible = 2

                # Open the PowerPoint presentation
                presentation = powerpoint.Presentations.Open(document.file.path, WithWindow=False)

                preview_folder = os.path.join(settings.MEDIA_ROOT, 'previews', f'document_{document_id}')
                os.makedirs(preview_folder, exist_ok=True)

                for slide_number, slide in enumerate(presentation.Slides):
                    # Save each slide as an image
                    img_path = os.path.join(preview_folder, f'slide_{slide_number + 1}.jpg')
                    slide.Export(img_path, "JPG", ScaleWidth=1024)
                    slides.append({
                        'number': slide_number + 1,
                        'image': f"{settings.MEDIA_URL}previews/document_{document_id}/slide_{slide_number + 1}.jpg"
                    })

                # Close the presentation and PowerPoint application
                presentation.Close()
                powerpoint.Quit()
                pythoncom.CoUninitialize()

            finally:
                # Выполняем разблокировку и уведомление ожидающему потоку
                condition.notify()

    return render(request, 'presentations/sample_preview.html', {'slides': slides, 'document': document})


@transaction.atomic
@login_required
def sample_download(request, document_id):
    document = get_object_or_404(SampleDocument, pk=document_id)
    file_path = document.file.path
    response = FileResponse(open(file_path, 'rb'), as_attachment=True, filename=document.description + '.pptx')
    return response


@transaction.atomic
@login_required
def document_download(request, document_id):
    document = get_object_or_404(Document, pk=document_id)
    if not (document.author == request.user or request.user.is_superuser or request.user.role == 'admin'):
        return handler403(request, PermissionDenied)
    file_path = document.file.path
    response = FileResponse(open(file_path, 'rb'), as_attachment=True, filename=document.description + '.pptx')
    return response


@transaction.atomic
@login_required
def document_delete(request, document_id):
    document = get_object_or_404(Document, pk=document_id)
    if not (document.author == request.user or request.user.is_superuser or request.user.role == 'admin'):
        return handler403(request, PermissionDenied)
    if request.method == 'POST':
        document_path = document.file.path
        os.remove(document_path)
        document.delete()
        success_message = "Документ успешно удален."
        messages.success(request, success_message)
        return redirect('powerpoint:document')
    if request.user == document.author or request.user.is_superuser or request.user.role == 'admin':
        return render(request, 'presentations/document_delete.html', {'document_id': document_id, 'document': document})
    else:
        return handler403(request, PermissionDenied)


@transaction.atomic
@login_required
def document(request):
    if request.method == 'GET':
        form = DocumentAddForm()
        if request.user.is_superuser or request.user.role == 'admin':
            documents = Document.objects.all().order_by('-pub_date')
        else:
            documents = Document.objects.filter(author=request.user).order_by('-pub_date')
        paginator = Paginator(documents, 8)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context = {'user': request.user, 'form': form, 'page_obj': page_obj}
        messages_list = list(messages.get_messages(request))
        context['success_message'] = next((msg.message for msg in messages_list if msg.level == messages.SUCCESS), None)
        context['error_message'] = next((msg.message for msg in messages_list if msg.level == messages.ERROR), None)
        messages.get_messages(request).used = True
        return render(request, 'presentations/document.html', context)
    if request.method == 'POST':
        form = DocumentAddForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.author = request.user
            document.save()
            success_message = "Документ успешно загружен."
            messages.success(request, success_message)
            return redirect('powerpoint:document')
        else:
            error_message = "Произошла ошибка при сохранении формы.<br>Возможно, вы выбрали не тот формат документа.<br>Проверьте данные и попробуйте ввести еще раз."
            messages.error(request, error_message)
            return redirect('powerpoint:merge')
    return render(request, 'presentations/document.html', {'form': form})


@transaction.atomic
def document_edit(request, document_id):
    document = get_object_or_404(Document, pk=document_id)
    document_path = document.file.path
    name = os.path.basename(document_path)
    if not (document.author == request.user or request.user.is_superuser or request.user.role == 'admin'):
        return handler403(request, PermissionDenied)
    if request.method == 'GET':
        form = DocumentAddForm(request.FILES, instance=document)
        return render(request, 'presentations/document_edit.html', {'form': form, 'document': document, 'name': name})
    if request.method == 'POST':
        form = DocumentAddForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            document = form.save(commit=False)
            document.author = request.user
            document.pub_date = timezone.now()
            document.save()
            full_path = document.file.path
            if full_path != document_path:
                os.remove(document_path)
            success_message = "Данные документа успешно изменены."
            messages.success(request, success_message)
            return redirect('powerpoint:document')
        else:
            error_message = "Произошла ошибка при сохранении формы.<br>Возможно, вы выбрали не тот формат документа.<br>Проверьте данные и попробуйте ввести еще раз."
            messages.error(request, error_message)
            return redirect('powerpoint:document')


@transaction.atomic
@login_required
def document_preview(request, document_id):
    document = get_object_or_404(Document, pk=document_id)
    if not (document.author == request.user or request.user.is_superuser or request.user.role == 'admin'):
        return handler403(request, PermissionDenied)

    slides = []

    with powerpoint_lock:
        # Захватываем блокировку powerpoint_lock и ожидаем условия
        with condition:
            # Если уже есть другой запрос на обработку, ожидаем его завершения
            while condition.wait(timeout=1):
                pass

            try:
                old_preview_folder = os.path.join(settings.MEDIA_ROOT, 'previews')
                if os.path.exists(old_preview_folder):
                    shutil.rmtree(old_preview_folder)

                # Ensure Python COM is initialized
                pythoncom.CoInitialize()

                # Initialize PowerPoint application
                powerpoint = win32com.client.Dispatch("PowerPoint.Application")
                powerpoint.Visible = 2

                # Open the PowerPoint presentation
                presentation = powerpoint.Presentations.Open(document.file.path, WithWindow=False)

                preview_folder = os.path.join(settings.MEDIA_ROOT, 'previews', f'document_{document_id}')
                os.makedirs(preview_folder, exist_ok=True)

                for slide_number, slide in enumerate(presentation.Slides):
                    # Save each slide as an image
                    img_path = os.path.join(preview_folder, f'slide_{slide_number + 1}.jpg')
                    slide.Export(img_path, "JPG", ScaleWidth=1024)
                    slides.append({
                        'number': slide_number + 1,
                        'image': f"{settings.MEDIA_URL}previews/document_{document_id}/slide_{slide_number + 1}.jpg"
                    })

                # Close the presentation and PowerPoint application
                presentation.Close()
                powerpoint.Quit()
                pythoncom.CoUninitialize()

            finally:
                # Выполняем разблокировку и уведомление ожидающему потоку
                condition.notify()

    return render(request, 'presentations/document_preview.html', {'slides': slides, 'document': document})


@transaction.atomic
@login_required
def merge_preview(request, document_id):
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return handler403(request, PermissionDenied)
    document = get_object_or_404(MainDocument, pk=document_id)

    slides = []

    with powerpoint_lock:
        # Захватываем блокировку powerpoint_lock и ожидаем условия
        with condition:
            # Если уже есть другой запрос на обработку, ожидаем его завершения
            while condition.wait(timeout=1):
                pass

            try:
                old_preview_folder = os.path.join(settings.MEDIA_ROOT, 'previews')
                if os.path.exists(old_preview_folder):
                    shutil.rmtree(old_preview_folder)

                # Ensure Python COM is initialized
                pythoncom.CoInitialize()

                # Initialize PowerPoint application
                powerpoint = win32com.client.Dispatch("PowerPoint.Application")
                powerpoint.Visible = 2

                # Open the PowerPoint presentation
                presentation = powerpoint.Presentations.Open(document.file.path, WithWindow=False)

                preview_folder = os.path.join(settings.MEDIA_ROOT, 'previews', f'document_{document_id}')
                os.makedirs(preview_folder, exist_ok=True)

                for slide_number, slide in enumerate(presentation.Slides):
                    # Save each slide as an image
                    img_path = os.path.join(preview_folder, f'slide_{slide_number + 1}.jpg')
                    slide.Export(img_path, "JPG", ScaleWidth=1024)
                    slides.append({
                        'number': slide_number + 1,
                        'image': f"{settings.MEDIA_URL}previews/document_{document_id}/slide_{slide_number + 1}.jpg"
                    })

                # Close the presentation and PowerPoint application
                presentation.Close()
                powerpoint.Quit()
                pythoncom.CoUninitialize()

            finally:
                # Выполняем разблокировку и уведомление ожидающему потоку
                condition.notify()

    return render(request, 'presentations/maindocument_preview.html', {'slides': slides, 'document': document})


@transaction.atomic
@login_required
def merge_download(request, document_id):
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return handler403(request, PermissionDenied)
    document = get_object_or_404(MainDocument, pk=document_id)
    file_path = document.file.path
    document_name = document.file.name
    parts = document_name.split('_')
    new_name = parts[0] + '.pptx'
    response = FileResponse(open(file_path, 'rb'), as_attachment=True, filename=new_name)
    return response


@transaction.atomic
@login_required
def merge_delete(request, document_id):
    document = get_object_or_404(MainDocument, pk=document_id)
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return handler403(request, PermissionDenied)
    if request.user.role in ['admin', 'moder'] and request.user != document.author:
        return handler403(request, PermissionDenied)
    if request.method == 'POST' and (request.user == document.author or request.user.is_superuser):
        document_path = document.file.path
        os.remove(document_path)
        document.delete()
        success_message = "Документ успешно удален."
        messages.success(request, success_message)
        return redirect('powerpoint:merge')
    if request.user == document.author or request.user.is_superuser or request.user.role == 'admin':
        return render(request, 'presentations/maindocument_delete.html', {'document_id': document_id, 'document': document})
    else:
        return handler403(request, PermissionDenied)


@transaction.atomic
@login_required
def merge(request):
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return handler403(request, PermissionDenied)
    if request.method == 'GET':
        form = MergePresentationForm()
        documents = MainDocument.objects.filter(author=request.user).order_by('-pub_date')
        paginator = Paginator(documents, 8)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context = {'user': request.user, 'form': form, 'page_obj': page_obj}
        messages_list = list(messages.get_messages(request))
        context['success_message'] = next((msg.message for msg in messages_list if msg.level == messages.SUCCESS), None)
        context['error_message'] = next((msg.message for msg in messages_list if msg.level == messages.ERROR), None)
        messages.get_messages(request).used = True
        return render(request, 'presentations/maindocument.html', context)
    if request.method == 'POST':
        form = MergePresentationForm(request.POST)
        if form.is_valid():
            selected_presentations = form.cleaned_data['presentations']
            sample_start = form.cleaned_data['sample_start']
            sample_end = form.cleaned_data['sample_end']
            if sample_start and sample_end:
                paths = [doc.file.path for doc in sample_start] + [doc.file.path for doc in selected_presentations] + [doc.file.path for doc in sample_end]
            elif len(sample_start) != 0:
                paths = [doc.file.path for doc in sample_start] + [doc.file.path for doc in selected_presentations]
            elif len(sample_end) != 0:
                paths = [doc.file.path for doc in selected_presentations] + [doc.file.path for doc in sample_end]
            else:
                paths = [doc.file.path for doc in selected_presentations]
            output_directory = "media/maindocuments"
            if not os.path.exists(output_directory):
                os.makedirs(output_directory)
            unique_name = os.path.join(output_directory, f"{form.cleaned_data['description']}_{uuid.uuid4().hex}.pptx")
            relative_path = get_relative_path(unique_name)
            main_document = MainDocument(
                author=request.user,
                file=relative_path,
                description=form.cleaned_data['description'],
            )
            main_document.save()
            merge_presentations_list(paths, unique_name)
            success_message = "Документ успешно сформирован."
            messages.success(request, success_message)
            return redirect('powerpoint:merge')
        else:
            error_message = "Произошла ошибка при сохранении формы.<br>Проверьте данные и попробуйте ввести еще раз."
            messages.error(request, error_message)
            return redirect('powerpoint:merge')
    else:
        form = MergePresentationForm()

    return render(request, 'presentations/maindocument.html', {'form': form})


def protected_media_view(request, path):
    if not request.user.is_authenticated:
        return handler403(request, PermissionDenied)

    full_path = os.path.join(settings.MEDIA_ROOT, path)
    if not os.path.exists(full_path):
        raise handler404(request, BadRequest)

    with open(full_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(full_path)}"'
        return response


def get_relative_path(full_path, base_folder="media"):
    """
    Возвращает относительный путь относительно базовой папки.

    :param full_path: Полный путь к файлу.
    :param base_folder: Базовая папка, относительно которой нужно получить относительный путь.
    :return: Относительный путь.
    """
    base_path = os.path.abspath(base_folder)
    relative_path = os.path.relpath(full_path, base_path)
    return relative_path


def merge_presentations_list(presentations, output_file):
    pythoncom.CoInitialize()
    Application = win32com.client.Dispatch("PowerPoint.Application")
    Application.WindowState = 2  # Minimize the PowerPoint application window
    outputPresentation = Application.Presentations.Add()
    outputPresentation.SaveAs(os.path.abspath(output_file))

    for file in presentations:
        currentPresentation = Application.Presentations.Open(file)
        currentPresentation.Slides.Range(range(1, currentPresentation.Slides.Count+1)).copy()
        Application.Presentations(output_file).Windows(1).Activate()
        outputPresentation.Application.CommandBars.ExecuteMso("PasteSourceFormatting")
        currentPresentation.Close()

    outputPresentation.save()
    outputPresentation.close()
    Application.Quit()
    pythoncom.CoUninitialize()
