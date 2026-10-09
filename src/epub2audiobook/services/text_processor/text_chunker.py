from typing import List
import spacy

from shared.schemas import ChunkType, TextChunk


class TextChunker:
    """Clase encargada de segmentar texto limpio en bloques sintácticos (chunks)

    optimizados para la inferencia del motor TTS.
    """

    def __init__(
        self,
        model_name: str = "es_core_news_sm",
        max_chars: int = 250,
        min_chars: int = 50,
    ):
        self.max_chars = max_chars
        self.min_chars = min_chars

        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            raise RuntimeError(
                f"El modelo de spaCy '{model_name}' no está instalado. "
                f"Ejecuta: uv run python -m spacy download {model_name}"
            )

        # Agregar el segmentador ultrarrápido basado en reglas
        if "sentencizer" not in self.nlp.pipe_names:
            self.nlp.add_pipe("sentencizer")

        # Desactivar componentes pesados que no requerimos para segmentación
        pipes_to_disable = [
            pipe for pipe in ["tok2vec", "morphologizer", "parser", "attribute_ruler", "lemmatizer", "ner"]
            if pipe in self.nlp.pipe_names
        ]
        if pipes_to_disable:
            self.nlp.disable_pipes(*pipes_to_disable)
            
    def create_chunks(
        self, text: str, book_id: str, chapter_index: int
    ) -> List[TextChunk]:
        """Divide el texto del capítulo en oraciones y las agrupa en TextChunk

        respetando el límite de caracteres max_chars.
        """
        if not text:
            return []

        doc = self.nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]

        chunks: List[TextChunk] = []
        current_sentences: List[str] = []
        current_len = 0
        chunk_sequence = 1

        for sentence in sentences:
            sentence_len = len(sentence)

            # Si una sola oración supera max_chars, la agregamos directamente
            if sentence_len > self.max_chars:
                if current_sentences:
                    chunks.append(
                        self._build_chunk(
                            sentences=current_sentences,
                            book_id=book_id,
                            chapter_index=chapter_index,
                            chunk_index=chunk_sequence,
                        )
                    )
                    chunk_sequence += 1
                    current_sentences = []
                    current_len = 0

                chunks.append(
                    self._build_chunk(
                        sentences=[sentence],
                        book_id=book_id,
                        chapter_index=chapter_index,
                        chunk_index=chunk_sequence,
                    )
                )
                chunk_sequence += 1
                continue

            # Verificar si agregar la oración excede el límite acumulado
            if current_len + sentence_len + 1 > self.max_chars and current_sentences:
                chunks.append(
                    self._build_chunk(
                        sentences=current_sentences,
                        book_id=book_id,
                        chapter_index=chapter_index,
                        chunk_index=chunk_sequence,
                    )
                )
                chunk_sequence += 1
                current_sentences = [sentence]
                current_len = sentence_len
            else:
                current_sentences.append(sentence)
                current_len += sentence_len + 1

        # Agregar el último bloque pendiente
        if current_sentences:
            chunks.append(
                self._build_chunk(
                    sentences=current_sentences,
                    book_id=book_id,
                    chapter_index=chapter_index,
                    chunk_index=chunk_sequence,
                )
            )

        return chunks

    def _build_chunk(
        self,
        sentences: List[str],
        book_id: str,
        chapter_index: int,
        chunk_index: int,
    ) -> TextChunk:
        """Crea una instancia válida del esquema Pydantic TextChunk."""
        full_text = " ".join(sentences).strip()
        chunk_id = f"{book_id}_c{chapter_index:03d}_k{chunk_index:04d}"

        # Detección básica de diálogo (si empieza o contiene guiones de diálogo)
        is_dialogue = full_text.startswith("-") or '"' in full_text
        chunk_type = ChunkType.DIALOGUE if is_dialogue else ChunkType.NARRATIVE

        return TextChunk(
            chunk_id=chunk_id,
            book_id=book_id,
            chapter_index=chapter_index,
            chunk_index=chunk_index,
            text=full_text,
            char_count=len(full_text),
            chunk_type=chunk_type,
        )