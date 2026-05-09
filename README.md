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
git clone https://github.com/arturbomtempo-dev/traduz-ai.git
cd traduz-ai

cat > .env <<EOF
DEBUG=True
SECRET_KEY=2xY8mQ9vL3kP7sR1nT6aF0wZ4cH8uJ5eB2gD9qM1rX7pK4vN
EOF

python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py runserver
```

Open [http://127.0.0.1:8000/translate/](http://127.0.0.1:8000/translate/) in your browser.

## License

Copyright (c) 2026 Artur Bomtempo

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
