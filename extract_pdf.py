from __future__ import annotations

import os
from pathlib import Path

import fitz


def extract_pdf_pages(pdf_path: str | os.PathLike[str]) -> dict[int, str]:
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f'Le fichier PDF est introuvable : {pdf_path}')

    doc = fitz.open(str(path))
    pages: dict[int, str] = {}
    for page_number in range(doc.page_count):
        text = doc[page_number].get_text('text')
        pages[page_number + 1] = text.strip()
    doc.close()
    return pages
