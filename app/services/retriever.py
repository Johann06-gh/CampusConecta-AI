from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.services.document_loader import DocumentChunk


@dataclass(frozen=True)
class SearchResult:
    chunk: DocumentChunk
    score: float


SPANISH_STOPWORDS = {
    "a", "al", "algo", "como", "con", "cual", "de", "del", "desde", "donde",
    "el", "ella", "en", "es", "esta", "este", "hay", "la", "las", "lo", "los",
    "me", "mi", "para", "por", "que", "qué", "se", "si", "sin", "su", "un",
    "una", "y", "ya", "puedo", "quiero", "necesito", "sobre",
}


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.lower())
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9áéíóúñü]+", " ", without_accents).strip()


def meaningful_terms(value: str) -> set[str]:
    return {
        token
        for token in normalize_text(value).split()
        if len(token) > 2 and token not in SPANISH_STOPWORDS
    }


class HybridRetriever:
    """Combines TF-IDF semantic similarity with an explicit keyword overlap bonus."""

    def __init__(self, chunks: list[DocumentChunk]):
        if not chunks:
            raise ValueError("Se requiere al menos un fragmento para crear el índice.")

        self.chunks = chunks
        self.vectorizer = TfidfVectorizer(
            strip_accents="unicode",
            lowercase=True,
            ngram_range=(1, 2),
            min_df=1,
            sublinear_tf=True,
        )
        self.matrix = self.vectorizer.fit_transform(chunk.text for chunk in chunks)
        self._term_sets = [meaningful_terms(chunk.text) for chunk in chunks]

    def search(self, query: str, top_k: int = 4) -> list[SearchResult]:
        clean_query = query.strip()
        if not clean_query:
            return []

        query_vector = self.vectorizer.transform([clean_query])
        semantic_scores = cosine_similarity(query_vector, self.matrix).flatten()
        query_terms = meaningful_terms(clean_query)

        keyword_scores = np.array(
            [
                len(query_terms.intersection(terms)) / max(len(query_terms), 1)
                for terms in self._term_sets
            ],
            dtype=float,
        )
        final_scores = (semantic_scores * 0.82) + (keyword_scores * 0.18)
        ranking = np.argsort(final_scores)[::-1][: max(top_k, 1)]

        return [
            SearchResult(chunk=self.chunks[index], score=float(final_scores[index]))
            for index in ranking
        ]
