from pathlib import Path

from app.services.document_loader import DocumentLoader
from app.services.retriever import HybridRetriever


DATA = Path(__file__).resolve().parents[1] / "data" / "servicios_estudiantiles.csv"


def test_csv_is_loaded():
    chunks = DocumentLoader().load(DATA)
    assert len(chunks) == 30
    assert chunks[0].metadata["service"] == "Tutorías de Matemática"


def test_retriever_finds_cv_service():
    chunks = DocumentLoader().load(DATA)
    retriever = HybridRetriever(chunks)
    results = retriever.search("quiero mejorar mi currículum para postular a prácticas")
    assert results
    assert results[0].chunk.metadata["service"] == "Revisión de CV"


def test_retriever_finds_laptop_service():
    chunks = DocumentLoader().load(DATA)
    retriever = HybridRetriever(chunks)
    results = retriever.search("¿puedo pedir una computadora prestada?")
    assert results[0].chunk.metadata["service"] == "Préstamo de laptops"
