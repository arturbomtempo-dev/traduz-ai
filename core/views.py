from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from deep_translator import GoogleTranslator

def index(request):
    return render(request, 'core/index.html')


def traduzir(request):
    if request.method == 'POST' and not request.FILES.get('arquivo'):
        return render(request, 'core/index.html', {'erro': 'Selecione um arquivo .txt antes de continuar.'})

    if request.method == 'POST' and request.FILES.get('arquivo'):
        arquivo = request.FILES['arquivo']

        fs = FileSystemStorage()
        filename = fs.save(arquivo.name, arquivo)
        file_path = fs.path(filename)

        # Lendo arquivo
        with open(file_path, 'r', encoding='utf-8') as f:
            texto = f.read()

        # Traduzindo
        traduzido = GoogleTranslator(source='en', target='pt').translate(texto)

        # Salvando arquivo traduzido
        novo_nome = f"traduzido_{arquivo.name}"
        novo_caminho = fs.path(novo_nome)

        with open(novo_caminho, 'w', encoding='utf-8') as f:
            f.write(traduzido)

        return render(request, 'core/resultado.html', {
            'texto': traduzido,
            'arquivo': fs.url(novo_nome)
        })

    return render(request, 'core/index.html')
