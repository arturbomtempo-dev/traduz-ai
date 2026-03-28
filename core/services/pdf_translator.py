import logging
import time

import fitz
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)

BATCH_CHAR_LIMIT = 8_000
BATCH_SEP = '\n||||\n'
API_DELAY = 0.05
MIN_FONT_SIZE = 5


def _safe_font(font_name: str) -> str:
    n = font_name.lower()
    if 'bold' in n and ('italic' in n or 'oblique' in n):
        return 'tibi'
    if 'bold' in n:
        return 'tibo'
    if 'italic' in n or 'oblique' in n:
        return 'tiit'
    if 'courier' in n or 'mono' in n or 'code' in n:
        return 'cour'
    if 'times' in n or 'serif' in n:
        return 'tiro'
    return 'helv'


def _extract_blocks(page: fitz.Page) -> list[dict]:
    records = []
    raw = page.get_text('dict', flags=fitz.TEXT_PRESERVE_WHITESPACE)

    for block in raw.get('blocks', []):
        if block.get('type') != 0:
            continue

        spans = [
            s
            for line in block.get('lines', [])
            for s in line.get('spans', [])
            if s.get('text', '').strip()
        ]
        if not spans:
            continue

        full_text = ' '.join(s['text'].strip() for s in spans)
        if not full_text.strip():
            continue

        dominant = max(spans, key=lambda s: s.get('size', 0))
        font_size = dominant.get('size', 12)
        if font_size < MIN_FONT_SIZE:
            continue

        records.append(
            {
                'bbox': fitz.Rect(block['bbox']),
                'text': full_text,
                'font_name': dominant.get('font', 'Helvetica'),
                'font_size': font_size,
                'color': dominant.get('color', 0),
            }
        )

    return records


def _chunk(texts: list[str]) -> list[list[str]]:
    batches: list[list[str]] = []
    current: list[str] = []
    length = 0

    for t in texts:
        if len(t) > BATCH_CHAR_LIMIT:
            if current:
                batches.append(current)
                current, length = [], 0
            batches.append([t])
            continue

        sep = len(BATCH_SEP) if current else 0
        if length + sep + len(t) > BATCH_CHAR_LIMIT:
            batches.append(current)
            current, length = [t], len(t)
        else:
            current.append(t)
            length += sep + len(t)

    if current:
        batches.append(current)
    return batches


def _translate_texts(texts: list[str], translator: GoogleTranslator) -> list[str]:
    results: list[str] = []

    for batch in _chunk(texts):
        joined = BATCH_SEP.join(batch)
        try:
            out = translator.translate(joined)
            if out is None:
                results.extend(batch)
            else:
                parts = out.split(BATCH_SEP.strip())
                if len(parts) == len(batch):
                    results.extend(p.strip() for p in parts)
                else:
                    for t in batch:
                        try:
                            r = translator.translate(t)
                            results.append(r if r else t)
                        except Exception:
                            results.append(t)
                        time.sleep(API_DELAY)
                    continue
        except Exception as exc:
            logger.warning('Batch translation failed (%s), keeping originals.', exc)
            results.extend(batch)

        time.sleep(API_DELAY)

    return results


def _int_to_rgb(v: int) -> tuple[float, float, float]:
    return ((v >> 16) & 0xFF) / 255, ((v >> 8) & 0xFF) / 255, (v & 0xFF) / 255


def _replace_text_on_page(
    page: fitz.Page,
    blocks: list[dict],
    translations: list[str],
) -> None:
    pairs = [(b, t) for b, t in zip(blocks, translations) if t and t != b['text']]
    if not pairs:
        return

    for block, _ in pairs:
        page.add_redact_annot(block['bbox'])
    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)

    for block, translated in pairs:
        _insert_text(page, block, translated)


def _insert_text(page: fitz.Page, block: dict, translated: str) -> None:
    bbox = block['bbox']
    font_size = block['font_size']
    color = _int_to_rgb(block['color'])
    font = _safe_font(block['font_name'])
    min_size = max(font_size * 0.6, MIN_FONT_SIZE)

    result = page.insert_textbox(
        bbox,
        translated,
        fontsize=font_size,
        fontname=font,
        color=color,
        align=fitz.TEXT_ALIGN_LEFT,
    )
    if result >= 0:
        return

    current = font_size - 1.0
    while current >= min_size:
        shape = page.new_shape()
        shape.draw_rect(bbox)
        shape.finish(color=None, fill=(1, 1, 1))
        shape.commit()

        result = page.insert_textbox(
            bbox,
            translated,
            fontsize=current,
            fontname=font,
            color=color,
            align=fitz.TEXT_ALIGN_LEFT,
        )
        if result >= 0:
            return
        current -= 1.0


def translate_pdf_bytes(pdf_bytes: bytes) -> bytes:
    translator = GoogleTranslator(source='en', target='pt')
    doc: fitz.Document = fitz.open(stream=pdf_bytes, filetype='pdf')
    total = doc.page_count
    logger.info('Translating PDF: %d pages.', total)

    try:
        for i in range(total):
            page = doc[i]
            blocks = _extract_blocks(page)
            if not blocks:
                continue

            translated = _translate_texts([b['text'] for b in blocks], translator)

            if len(translated) != len(blocks):
                logger.warning('Page %d: count mismatch, skipping.', i + 1)
                continue

            _replace_text_on_page(page, blocks, translated)
            logger.info('Page %d/%d done.', i + 1, total)

        return bytes(doc.write(garbage=3, deflate=True))
    finally:
        doc.close()
