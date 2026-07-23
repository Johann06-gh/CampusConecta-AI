from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pypdf import PdfReader


@dataclass(frozen=True)
class DocumentChunk:
    chunk_id: str
    text: str
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)


class DocumentLoader:
    """Loads CSV or PDF files and converts them into searchable chunks."""

    def load(self, path: Path) -> list[DocumentChunk]:
        if not path.exists():
            raise FileNotFoundError(f"No se encontró el documento: {path}")

        suffix = path.suffix.lower()
        if suffix == ".csv":
            return self._load_csv(path)
        if suffix == ".pdf":
            return self._load_pdf(path)

        raise ValueError("Formato no soportado. Usa un archivo CSV o PDF.")

    def _load_csv(self, path: Path) -> list[DocumentChunk]:
        chunks: list[DocumentChunk] = []
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            if not reader.fieldnames:
                raise ValueError("El CSV no contiene encabezados.")

            for row_number, row in enumerate(reader, start=1):
                clean_row = {
                    (key or "campo").strip(): (value or "").strip()
                    for key, value in row.items()
                }
                text = "\n".join(
                    f"{key.replace('_', ' ').title()}: {value}"
                    for key, value in clean_row.items()
                    if value
                )
                source_name = clean_row.get("servicio") or f"Fila {row_number}"
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"csv-{row_number}",
                        text=text,
                        source=source_name,
                        metadata={
                            "file": path.name,
                            "row": row_number,
                            "category": clean_row.get("categoria", ""),
                            "service": clean_row.get("servicio", ""),
                            "contact": clean_row.get("contacto", ""),
                            "url": clean_row.get("enlace", ""),
                            "raw": clean_row,
                        },
                    )
                )

        if not chunks:
            raise ValueError("El CSV está vacío.")
        return chunks

    def _load_pdf(self, path: Path) -> list[DocumentChunk]:
        reader = PdfReader(str(path))
        chunks: list[DocumentChunk] = []

        for page_number, page in enumerate(reader.pages, start=1):
            page_text = (page.extract_text() or "").strip()
            if not page_text:
                continue

            for section_number, section in enumerate(self._split_text(page_text), start=1):
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"pdf-{page_number}-{section_number}",
                        text=section,
                        source=f"{path.name}, página {page_number}",
                        metadata={
                            "file": path.name,
                            "page": page_number,
                            "section": section_number,
                        },
                    )
                )

        if not chunks:
            raise ValueError("No se pudo extraer texto del PDF.")
        return chunks

    @staticmethod
    def _split_text(text: str, max_chars: int = 1500, overlap: int = 180) -> list[str]:
        paragraphs = [part.strip() for part in text.split("\n") if part.strip()]
        sections: list[str] = []
        current = ""

        for paragraph in paragraphs:
            candidate = f"{current}\n{paragraph}".strip()
            if len(candidate) <= max_chars:
                current = candidate
                continue

            if current:
                sections.append(current)
                current = f"{current[-overlap:]}\n{paragraph}".strip()
            else:
                sections.append(paragraph[:max_chars])
                current = paragraph[max_chars - overlap :]

        if current:
            sections.append(current)
        return sections
