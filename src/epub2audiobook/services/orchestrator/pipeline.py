from pathlib import Path
from typing import Dict, List, Optional, Tuple

from shared.schemas import BookMetadata, ChunkType
from epub2audiobook.services.text_processor.pipeline import TextProcessorPipeline
from epub2audiobook.services.tts_engine.engine import TTSEngine
from epub2audiobook.services.audio_assembler.assembler import AudioAssembler


class AudiobookPipeline:
    """
    Principal orchestrator that connects the 3 core services
    to transform an EPUB file into a set of integrated chapter audios.
    """

    def __init__(
        self,
        lang_code: str = "e",
        default_voice: str = "ef_dora",
        max_chunk_chars: int = 220,
        chunk_silence_ms: int = 300,
        chapter_silence_ms: int = 1500,
    ):
        # Initialize the three core services of the pipeline
        self.text_pipeline = TextProcessorPipeline(max_chunk_chars=max_chunk_chars)
        self.tts_engine = TTSEngine(lang_code=lang_code, default_voice=default_voice)
        self.assembler = AudioAssembler(
            chunk_silence_ms=chunk_silence_ms,
            chapter_silence_ms=chapter_silence_ms,
        )

    def process_book(
        self,
        epub_path: str | Path,
        output_dir: str | Path,
        voice_mapping: Optional[Dict[ChunkType, str]] = None,
        export_format: str = "wav",
    ) -> Tuple[BookMetadata, List[Path]]:
        """Ejecuta la conversión completa de un EPUB a archivos de audio por capítulo.

        Args:
            epub_path: Ruta al archivo .epub de entrada.
            output_dir: Carpeta final donde se guardarán los audios ensamblados.
            voice_mapping: Mapeo opcional de voces por tipo de chunk (narrativa/diálogo).
            export_format: Formato de salida ('wav', 'mp3', etc.).

        Returns:
            Tupla con los metadatos del libro y la lista de rutas a los audios por capítulo.
        """
        epub_file = Path(epub_path)
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        # Carpeta temporal para los fragmentos .wav intermedios
        temp_chunks_dir = out_dir / "_temp_chunks"

        # 1. Procesar y limpiar texto del EPUB
        print("📖 [1/3] Extrayendo y segmentando texto del EPUB...")
        metadata, chapters = self.text_pipeline.process_epub(epub_file)

        final_audio_files: List[Path] = []

        # 2. Procesar capítulo por capítulo
        print(f"🎙️ [2/3] Sintetizando audio para {len(chapters)} capítulos...")
        for ch in chapters:
            if not ch.chunks:
                continue

            print(f"   ➔ Procesando: '{ch.title}' ({len(ch.chunks)} chunks)")

            # Carpeta temporal para los chunks del capítulo actual
            ch_temp_dir = temp_chunks_dir / f"ch_{ch.chapter_index:03d}"

            # Sintetizar chunks
            wav_chunks = self.tts_engine.synthesize_chunks(
                chunks=ch.chunks,
                output_dir=ch_temp_dir,
                voice_mapping=voice_mapping,
            )

            # 3. Ensamblar los audios del capítulo
            ch_output_file = out_dir / f"capitulo_{ch.chapter_index:03d}.{export_format}"
            assembled_path = self.assembler.assemble_chapter(
                wav_paths=wav_chunks,
                output_file=ch_output_file,
                export_format=export_format,
            )
            final_audio_files.append(assembled_path)

        print("🎉 [3/3] Proceso finalizado con éxito.")
        return metadata, final_audio_files