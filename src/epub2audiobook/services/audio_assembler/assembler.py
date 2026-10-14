from pathlib import Path
from typing import List, Optional
from pydub import AudioSegment

from shared.schemas import ChapterData


class AudioAssembler:
    """
    Service loaded with the responsibility of concatenating audio chunks (.wav),
     inserting dynamic silences, and exporting complete chapters/books.
    """

    def __init__(
        self,
        chunk_silence_ms: int = 300,   # Silence between sentences/chunks (0.3s)
        chapter_silence_ms: int = 1500 # Silence at the beginning/end of the chapter (1.5s)
    ):
        self.chunk_silence = AudioSegment.silent(duration=chunk_silence_ms)
        self.chapter_silence = AudioSegment.silent(duration=chapter_silence_ms)

    def assemble_chapter(
        self,
        wav_paths: List[Path | str],
        output_file: Path | str,
        export_format: str = "wav",
    ) -> Path:
        """
        Proccess and concatenate a list of ordered .wav files of a chapter into a single audio file.

        Args:
            wav_paths: List of ordered paths to the .wav files of the chunks.
            output_file: Path to the output file.
            export_format: Export format ('wav', 'mp3', 'm4b').

        Returns:
            Path to the assembled file.
        """
        # Create the output directory if it doesn't exist
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Validate that the list of audio files is not empty
        if not wav_paths:
            raise ValueError("The list of audio files is empty .")

        # Start with a chapter entry silence
        combined = AudioSegment.silent(duration=0) + self.chapter_silence

        # Iterate through the list of .wav files, load them, and concatenate them with silences
        for idx, wav_path in enumerate(wav_paths):
            path = Path(wav_path)
            if not path.exists():
                raise FileNotFoundError(f"Audio File not found: {path}")

            # Load audio segment
            segment = AudioSegment.from_wav(path)
            combined += segment

            # Add silence between chunks (except after the last one)
            if idx < len(wav_paths) - 1:
                combined += self.chunk_silence

        # Add silence at the end of the chapter
        combined += self.chapter_silence

        # Export to the desired format
        combined.export(output_path, format=export_format)

        return output_path