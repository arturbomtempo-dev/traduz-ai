# TraduzAí

![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-6.0-092E20?logo=django&logoColor=white)
![PyMuPDF](https://img.shields.io/badge/PyMuPDF-1.27-blue)
![Google Translate](https://img.shields.io/badge/Google%20Translate-API-4285F4?logo=googletranslate&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Render](https://img.shields.io/badge/Deploy-Render-46E3B7?logo=render&logoColor=white)

A fast, layout-preserving document translator. Upload a PDF or TXT file in English and get back a fully translated Portuguese version — with the original formatting intact.

## Features

- **PDF translation** with layout, columns, and font style preservation
- **TXT translation** with instant preview
- Batch translation engine for speed
- Clean, responsive UI with drag-and-drop upload
- One-click download of translated files

## Tech Stack

| Layer       | Technology                             |
| ----------- | -------------------------------------- |
| Backend     | Django, Gunicorn, WhiteNoise           |
| Translation | Google Translate (via deep-translator) |
| PDF Engine  | PyMuPDF (fitz)                         |
| Frontend    | HTML, CSS, JavaScript                  |
| Deploy      | Render                                 |

## Getting Started

```bash
git clone https://github.comarturbomtempo-dev/traduz-ai.git
cd traduz-ai
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py runserver
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

## License

MIT
