from __future__ import annotations

import logging
from dataclasses import dataclass

from app.core.config import Settings
from app.services.document_loader import DocumentChunk, DocumentLoader
from app.services.retriever import HybridRetriever, SearchResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AgentAnswer:
    answer: str
    mode: str
    results: list[SearchResult]


class CampusAgent:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.loader = DocumentLoader()
        self.chunks: list[DocumentChunk] = self.loader.load(settings.data_path)
        self.retriever = HybridRetriever(self.chunks)

    def answer(self, question: str) -> AgentAnswer:
        results = self.retriever.search(question, top_k=self.settings.top_k)
        relevant = [result for result in results if result.score >= self.settings.min_relevance]

        if not relevant:
            return AgentAnswer(
                answer=(
                    "No encontré información suficiente en el documento para responder esa pregunta. "
                    "Prueba mencionando el nombre del servicio, trámite o beneficio que buscas."
                ),
                mode="document_not_found",
                results=results,
            )

        if self.settings.gemini_api_key:
            try:
                return AgentAnswer(
                    answer=self._answer_with_gemini(question, relevant),
                    mode="gemini_rag",
                    results=relevant,
                )
            except Exception as exc:  # pragma: no cover - depends on external API
                logger.exception("Gemini request failed: %s", exc)
                if not self.settings.allow_fallback:
                    raise

        return AgentAnswer(
            answer=self._fallback_answer(question, relevant),
            mode="extractive_fallback",
            results=relevant,
        )

    def reload(self) -> int:
        self.chunks = self.loader.load(self.settings.data_path)
        self.retriever = HybridRetriever(self.chunks)
        return len(self.chunks)

    def _answer_with_gemini(self, question: str, results: list[SearchResult]) -> str:
        from google import genai

        client = genai.Client(api_key=self.settings.gemini_api_key)
        context = self._build_context(results)
        prompt = f"""
Eres CampusConecta AI, un agente especializado en orientar estudiantes.
Responde en español claro y amable usando EXCLUSIVAMENTE el contexto proporcionado.
No inventes requisitos, horarios, precios, enlaces ni beneficios.
Cuando uses información de un bloque, añade la referencia [Fuente N].
Si el contexto no basta, indícalo expresamente.

CONTEXTO:
{context}

PREGUNTA DEL USUARIO:
{question}

FORMATO DE RESPUESTA:
- Respuesta directa en uno o dos párrafos breves.
- Pasos o requisitos en viñetas solo cuando ayuden.
- Termina con las fuentes usadas, por ejemplo: Fuentes: [Fuente 1], [Fuente 2].
""".strip()

        response = client.models.generate_content(
            model=self.settings.gemini_model,
            contents=prompt,
        )
        text = (response.text or "").strip()
        if not text:
            raise RuntimeError("Gemini devolvió una respuesta vacía.")
        return text

    @staticmethod
    def _build_context(results: list[SearchResult]) -> str:
        blocks = []
        for index, result in enumerate(results, start=1):
            blocks.append(
                f"[Fuente {index}]\nOrigen: {result.chunk.source}\n{result.chunk.text}"
            )
        return "\n\n".join(blocks)

    @staticmethod
    def _fallback_answer(question: str, results: list[SearchResult]) -> str:
        primary = results[0].chunk.metadata.get("raw", {})
        service = primary.get("servicio") or results[0].chunk.source
        description = primary.get("descripcion") or results[0].chunk.text
        requirements = primary.get("requisitos", "No especificado")
        modality = primary.get("modalidad", "No especificada")
        schedule = primary.get("horario", "No especificado")
        contact = primary.get("contacto", "No especificado")
        url = primary.get("enlace", "")

        related = [result.chunk.source for result in results[1:3]]
        lines = [
            f"La opción más relacionada con tu pregunta es **{service}**. {description}",
            "",
            f"- **Requisitos:** {requirements}",
            f"- **Modalidad:** {modality}",
            f"- **Horario:** {schedule}",
            f"- **Contacto:** {contact}",
        ]
        if url:
            lines.append(f"- **Enlace:** {url}")
        if related:
            lines.extend(["", f"También podrían servirte: {', '.join(related)}."])
        lines.extend(
            [
                "",
                "_Respuesta generada en modo de respaldo con la información recuperada del documento._",
                "Fuentes: [Fuente 1]" + (", [Fuente 2]" if len(results) > 1 else ""),
            ]
        )
        return "\n".join(lines)
