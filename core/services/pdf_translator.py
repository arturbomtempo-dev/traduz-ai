import logging
import time

import fitz
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)

BATCH_CHAR_LIMIT = 4_800
BATCH_SEP = '\n||||\n'
BATCH_SEP_STRIP = '||||'
API_DELAY = 0.02
MIN_FONT_SIZE = 4
FONT_SIZE_STEP = 1.0
BBOX_PAD = 1.0


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


def _int_to_rgb(v: int) -> tuple[float, float, float]:
    return ((v >> 16) & 0xFF) / 255, ((v >> 8) & 0xFF) / 255, (v & 0xFF) / 255


def _extract_blocks(page: fitz.Page) -> list[dict]:
    """Extract text blocks from a page.

    Each block maps to a contiguous text region. PyMuPDF already creates
    separate blocks for separate columns, so multi-column layouts are
    handled naturally.
    """
    raw = page.get_text('dict', flags=fitz.TEXT_PRESERVE_WHITESPACE)
    records = []

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

        records.append({
            'bbox': fitz.Rect(block['bbox']),
            'text': full_text,
            'font_name': dominant.get('font', 'Helvetica'),
            'font_size': font_size,
            'color': dominant.get('color', 0),
        })

    return records


def _chunk(texts: list[str]) -> list[list[str]]:
    batches: list[list[str]] = []
    current: list[str] = []
    length = 0
    sep_len = len(BATCH_SEP)

    for t in texts:
        if len(t) > BATCH_CHAR_LIMIT:
            if current:
                batches.append(current)
                current, length = [], 0
            batches.append([t])
            continue

        added = (sep_len if current else 0) + len(t)
        if length + added > BATCH_CHAR_LIMIT:
            batches.append(current)
            current, length = [t], len(t)
        else:
            current.append(t)
            length += added

    if current:
        batches.append(current)
    return batches


def _translate_one(text: str, translator: GoogleTranslator) -> str:
    try:
        result = translator.translate(text)
        return result.strip() if result else text
    except Exception:
        return text


def _translate_texts(texts: list[str], translator: GoogleTranslator) -> list[str]:
    if not texts:
        return []

    results: list[str] = []

    for batch in _chunk(texts):
        joined = BATCH_SEP.join(batch)
        translated_ok = False

        try:
            out = translator.translate(joined)
            if out is not None:
                parts = out.split(BATCH_SEP_STRIP)
                if len(parts) == len(batch):
                    results.extend(p.strip() for p in parts)
                    translated_ok = True
        except Exception as exc:
            logger.warning('Batch translation failed: %s', exc)

        if not translated_ok:
            for t in batch:
                results.append(_translate_one(t, translator))
                time.sleep(API_DELAY)
            continue

        time.sleep(API_DELAY)

    return results


def _replace_text_on_page(
    page: fitz.Page,
    blocks: list[dict],
    translations: list[str],
) -> None:
    """Remove original text and insert translations.

    Uses a two-phase approach:
    1. Redact text objects from the PDF (removes the selectable text layer).
    2. Draw opaque white rectangles over each block area to cover any
       underlying images or graphics that may still show original text.
    3. Write translated text on top using TextWriter.
    """
    pairs = [
        (blk, trans)
        for blk, trans in zip(blocks, translations)
        if trans and trans.strip() != blk['text'].strip()
    ]
    if not pairs:
        return

    # Phase 1: redact text objects
    for blk, _ in pairs:
        page.add_redact_annot(blk['bbox'])
    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)

    # Phase 2: cover background with white rects, then insert translated text
    for blk, translated in pairs:
        _cover_and_insert(page, blk, translated)


def _cover_and_insert(page: fitz.Page, block: dict, translated: str) -> None:
    """Draw white rectangle over block area, then insert translated text."""
    bbox = block['bbox']

    if bbox.is_empty or bbox.width < 1 or bbox.height < 1:
        return

    padded = fitz.Rect(
        bbox.x0 - BBOX_PAD,
        bbox.y0 - BBOX_PAD,
        bbox.x1 + BBOX_PAD,
        bbox.y1 + BBOX_PAD,
    )

    # Clip to page boundaries
    padded = padded & page.rect

    # Draw opaque white background to cover any underlying image/text
    shape = page.new_shape()
    shape.draw_rect(padded)
    shape.finish(color=None, fill=(1, 1, 1))
    shape.commit()

    # Insert translated text using TextWriter (dry-run until it fits)
    max_size = block['font_size']
    color = _int_to_rgb(block['color'])
    font_name = _safe_font(block['font_name'])
    min_size = max(max_size * 0.5, MIN_FONT_SIZE)
    font = fitz.Font(font_name)

    target_size = max_size
    while target_size >= min_size:
        try:
            tw = fitz.TextWriter(page.rect)
            excess = tw.fill_textbox(
                bbox,
                translated,
                font=font,
                fontsize=target_size,
                align=fitz.TEXT_ALIGN_LEFT,
            )
            if not excess:
                tw.write_text(page, color=color)
                return
        except ValueError:
            break
        target_size -= FONT_SIZE_STEP

    # Fallback: use insert_textbox which handles tight bboxes better
    _insert_textbox_fallback(page, bbox, translated, min_size, font_name, color)


def _insert_textbox_fallback(
    page: fitz.Page,
    bbox: fitz.Rect,
    text: str,
    fontsize: float,
    fontname: str,
    color: tuple[float, float, float],
) -> None:
    """Fallback insertion using page.insert_textbox for tight bounding boxes."""
    size = fontsize
    while size >= MIN_FONT_SIZE:
        rc = page.insert_textbox(
            bbox,
            text,
            fontsize=size,
            fontname=fontname,
            color=color,
            align=fitz.TEXT_ALIGN_LEFT,
        )
        if rc >= 0:
            return
        size -= FONT_SIZE_STEP

    # Last resort: insert at minimum size regardless of overflow
    page.insert_textbox(
        bbox,
        text,
        fontsize=MIN_FONT_SIZE,
        fontname=fontname,
        color=color,
        align=fitz.TEXT_ALIGN_LEFT,
    )


def translate_pdf_bytes(pdf_bytes: bytes) -> bytes:
    translator = GoogleTranslator(source='en', target='pt')
    doc: fitz.Document = fitz.open(stream=pdf_bytes, filetype='pdf')
    total = doc.page_count
    logger.info('Translating PDF: %d pages.', total)

    try:
        # Phase 1: extract all blocks from all pages
        page_blocks: list[list[dict]] = []
        all_texts: list[str] = []

        for i in range(total):
            blocks = _extract_blocks(doc[i])
            page_blocks.append(blocks)
            all_texts.extend(b['text'] for b in blocks)

        logger.info('Extracted %d text blocks total.', len(all_texts))

        if not all_texts:
            return bytes(doc.write(garbage=3, deflate=True))

        # Phase 2: translate everything in one pass
        all_translated = _translate_texts(all_texts, translator)

        # Phase 3: apply translations page by page
        offset = 0
        for i in range(total):
            blocks = page_blocks[i]
            if not blocks:
                continue

            count = len(blocks)
            translations = all_translated[offset:offset + count]
            offset += count

            _replace_text_on_page(doc[i], blocks, translations)
            logger.info('Page %d/%d done.', i + 1, total)

        return bytes(doc.write(garbage=3, deflate=True))
    finally:
        doc.close()
