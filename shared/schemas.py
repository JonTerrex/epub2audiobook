from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ChunkType(str, Enum):
    NARRATIVE = "narrative"
    DIALOGUE = "dialogue"
    HEADING = "heading"


class TextChunk(BaseModel):
    """Representa un fragmento de texto procesado e individual listo para síntesis TTS."""

    chunk_id: str = Field(
        ...,
        description="Identificador único global del chunk (ej. book123_ch01_0005)",
    )
    book_id: str = Field(..., description="Hash o ID único del libro")
    chapter_index: int = Field(
        ..., description="Índice numérico del capítulo"
    )
    chunk_index: int = Field(
        ..., description="Orden del chunk dentro del capítulo"
    )
    text: str = Field(
        ..., description="Texto limpio y normalizado para pasar al motor TTS"
    )
    char_count: int = Field(
        ..., description="Cantidad de caracteres del texto"
    )
    chunk_type: ChunkType = Field(
        default=ChunkType.NARRATIVE, description="Tipo de contenido"
    )


class ChapterData(BaseModel):
    """Representa la estructura procesada de un capítulo completo."""

    chapter_index: int
    title: str
    raw_text: str
    chunks: list[TextChunk] = []


class BookMetadata(BaseModel):
    """Metadatos globales extraídos del libro EPUB."""

    book_id: str
    title: str
    author: Optional[str] = "Desconocido"
    language: str = "es"
    total_chapters: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)