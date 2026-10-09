from pathlib import Path
from typing import List, Tuple

from shared.schemas import BookMetadata, ChapterData
from epub2audiobook.services.text_processor.epub_parser import EpubParser
from epub2audiobook.services.text_processor.text_cleaner import TextCleaner
from epub2audiobook.services.text_processor.text_chunker import TextChunker


class TextProcessorPipeline:
    """Orquestador principal del módulo text_processor.

    Coordina la extracción, limpieza fonética y chunking semántico de un EPUB.
    """

    def __init__(self, max_chunk_chars: int = 250):
        self.cleaner = TextCleaner(lang="es")
        self.chunker = TextChunker(max_chars=max_chunk_chars)

    def process_epub(
        self, epub_path: str | Path
    ) -> Tuple[BookMetadata, List[ChapterData]]:
        """Procesa un archivo EPUB completo y devuelve sus metadatos

        junto con la lista de capítulos estructurados y chunked.
        """
        # 1. Parsear EPUB y extraer metadatos
        parser = EpubParser(epub_path)
        metadata = parser.extract_metadata()
        raw_chapters = parser.extract_chapters()

        processed_chapters: List[ChapterData] = []

        # 2. Procesar capítulo por capítulo
        for ch in raw_chapters:
            # Limpieza fonética
            cleaned_text = self.cleaner.clean(ch.raw_text)

            # Segmentación en chunks
            chunks = self.chunker.create_chunks(
                text=cleaned_text,
                book_id=metadata.book_id,
                chapter_index=ch.chapter_index,
            )

            # Actualizar capítulo con chunks
            ch.chunks = chunks
            processed_chapters.append(ch)

        metadata.total_chapters = len(processed_chapters)
        return metadata, processed_chapters