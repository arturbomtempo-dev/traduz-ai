import io
import logging
import os
import uuid

from deep_translator import GoogleTranslator
from django.core.cache import cache
from django.http import FileResponse, Http404
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .services.pdf_translator import translate_pdf_bytes

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'.txt', '.pdf'}
MAX_UPLOAD_MB = 100
_CACHE_TTL = 600


def _get_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()


def _validate_upload(file_obj) -> str | None:
    if not file_obj:
        return 'Nenhum arquivo enviado.'
    ext = _get_extension(file_obj.name)
    if ext not in ALLOWED_EXTENSIONS:
        return f'Formato não suportado: {ext}. Envie um arquivo .txt ou .pdf.'
    size_mb = file_obj.size / (1024 * 1024)
    if size_mb > MAX_UPLOAD_MB:
        return f'Arquivo muito grande ({size_mb:.1f} MB). O limite é {MAX_UPLOAD_MB} MB.'
    return None


def index(request):
    return render(request, 'index.html')


@require_POST
def translate(request):
    file_obj = request.FILES.get('file')
    error = _validate_upload(file_obj)
    if error:
        return render(request, 'index.html', {'error': error})

    ext = _get_extension(file_obj.name)

    try:
        if ext == '.txt':
            return _handle_txt(request, file_obj)
        else:
            return _handle_pdf(request, file_obj)
    except Exception as exc:
        logger.exception('Translation failed for %s', file_obj.name)
        return render(
            request,
            'index.html',
            {'error': f'Erro durante a tradução: {exc}'},
        )


def _handle_txt(request, file_obj):
    text = file_obj.read().decode('utf-8')
    translated = GoogleTranslator(source='en', target='pt').translate(text)
    output_name = f'translated_{file_obj.name}'
    return render(
        request,
        'result.html',
        {
            'type': 'txt',
            'text': translated,
            'filename': output_name,
        },
    )


def _handle_pdf(request, file_obj):
    pdf_bytes = file_obj.read()
    translated = translate_pdf_bytes(pdf_bytes)
    output_name = f'translated_{file_obj.name}'
    token = uuid.uuid4().hex

    cache.set(
        f'pdf_{token}',
        {'data': translated, 'filename': output_name},
        timeout=_CACHE_TTL,
    )

    return render(
        request,
        'result.html',
        {
            'type': 'pdf',
            'token': token,
            'filename': output_name,
        },
    )


def download(request, token: str):
    if not token.isalnum() or len(token) != 32:
        raise Http404

    entry = cache.get(f'pdf_{token}')
    if not entry:
        raise Http404('Arquivo expirado ou não encontrado.')

    return FileResponse(
        io.BytesIO(entry['data']),
        content_type='application/pdf',
        as_attachment=True,
        filename=entry['filename'],
    )


def page_not_found(request, exception):
    return render(request, '404.html', status=404)
