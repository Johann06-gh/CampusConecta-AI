from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class QuestionRequest(BaseModel):
    question: str = Field(min_length=3, max_length=800)

    @field_validator("question")
    @classmethod
    def clean_question(cls, value: str) -> str:
        clean = value.strip()
        if not clean:
            raise ValueError("La pregunta no puede estar vacía.")
        return clean


class SourceItem(BaseModel):
    title: str
    file: str
    category: str | None = None
    page: int | None = None
    row: int | None = None
    contact: str | None = None
    url: str | None = None
    relevance: float
    excerpt: str


class QuestionResponse(BaseModel):
    answer: str
    mode: str
    sources: list[SourceItem]


class HealthResponse(BaseModel):
    status: str
    document: str
    chunks: int
    llm_enabled: bool
