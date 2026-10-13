from pathlib import Path
from typing import Optional
import soundfile as sf
from kokoro import KPipeline

from shared.schemas import TextChunk


class TTSEngine:
    """Motor de síntesis de voz impulsado por Kokoro-TTS.

    Recibe objetos TextChunk y genera sus correspondientes archivos de audio .wav.
    """

    def __init__(
        self,
        lang_code: str = "e",  # 'e' = español ('a' = inglés americano, 'b' = inglés británico)
        default_voice: str = "ef_dora",  # Voz femenina en español por defecto
        sample_rate: int = 24000,
    ):
        self.lang_code = lang_code
        self.default_voice = default_voice
        self.sample_rate = sample_rate

        # Inicializar la pipeline de Kokoro (descarga automáticamente el modelo si no existe)
        self.pipeline = KPipeline(lang_code=self.lang_code)

    def synthesize_chunk(
        self,
        chunk: TextChunk,
        output_dir: str | Path,
        voice: Optional[str] = None,
    ) -> Path:
        """Sintetiza un único TextChunk y guarda el archivo .wav en disk.

        Args:
            chunk: Objeto TextChunk con el texto normalizado y metadatos.
            output_dir: Directorio donde se guardará el audio resultante.
            voice: Nombre opcional de la voz a utilizar (sobrescribe la voz por defecto).

        Returns:
            Path al archivo .wav generado.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        selected_voice = voice or self.default_voice
        file_name = f"{chunk.chunk_id}.wav"
        destination_file = output_path / file_name

        # Kokoro procesa el texto y genera fragmentos de audio
        generator = self.pipeline(
            chunk.text,
            voice=selected_voice,
            speed=1.0,
            split_pattern=r"\n+",
        )

        audio_segments = []
        for _, _, audio in generator:
            audio_segments.append(audio)

        if not audio_segments:
            raise ValueError(f"No se pudo generar audio para el chunk {chunk.chunk_id}")

        # Concatenar segmentos de audio si el fragmento generó más de uno
        import numpy as np

        full_audio = np.concatenate(audio_segments) if len(audio_segments) > 1 else audio_segments[0]

        # Guardar el resultado en formato .wav (PCM 16-bit, 24kHz)
        sf.write(destination_file, full_audio, self.sample_rate)

        return destination_file