import hashlib
from pathlib import Path
from typing import List, Tuple
import ebooklib
from bs4 import BeautifulSoup
from ebooklib import epub

from shared.schemas import ChapterData, BookMetadata


class EpubParser:
    """Clase encargada del parseo, extracción de metadatos y filtrado inicial

    de capítulos de archivos EPUB.
    """

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(
                f"El archivo {self.file_path} no existe."
            )

        self.book = epub.read_epub(str(self.file_path))
        self.book_id = self._generate_book_id()

    def _generate_book_id(self) -> str:
        """Genera un ID único (hash SHA256) basado en el contenido del archivo."""
        hasher = hashlib.sha256()
        with open(self.file_path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()[:12]

    def extract_metadata(self) -> BookMetadata:
        """Extrae los metadatos principales del libro."""
        title = self.book.get_metadata("DC", "title")
        author = self.book.get_metadata("DC", "creator")
        language = self.book.get_metadata("DC", "language")

        return BookMetadata(
            book_id=self.book_id,
            title=title[0][0] if title else self.file_path.stem,
            author=author[0][0] if author else "Desconocido",
            language=language[0][0] if language else "es",
        )

    def extract_chapters(
        self, min_length_threshold: int = 150
    ) -> List[ChapterData]:
        """Recorre el documento HTML del EPUB, elimina etiquetas no narrativas

        y extrae los capítulos limpios.
        """
        chapters: List[ChapterData] = []
        chapter_index = 0

        for item in self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            raw_html = item.get_content()
            title, text = self._clean_html_content(raw_html)

            # Filtrar páginas irrelevantes o muy cortas (portadas, índices vacíos)
            if len(text) < min_length_threshold:
                continue

            chapter_index += 1
            chapter_title = (
                title if title else f"Capítulo {chapter_index}"
            )

            chapters.append(
                ChapterData(
                    chapter_index=chapter_index,
                    title=chapter_title,
                    raw_text=text,
                    chunks=[],
                )
            )

        return chapters

    def _clean_html_content(self, html_bytes: bytes) -> Tuple[str, str]:
        """Elimina etiquetas HTML superfluas (scripts, estilos, notas)

        y devuelve el título detectado y el texto plano.
        """
        soup = BeautifulSoup(html_bytes, "html.parser")

        # Eliminar elementos visuales o de apoyo que no deben leerse en audio
        for element in soup(["script", "style", "sup", "sub", "footer", "nav"]):
            element.decompose()

        # Extraer posible título de capítulo dentro de etiquetas h1/h2
        header = soup.find(["h1", "h2", "h3"])
        title = header.get_text(strip=True) if header else ""

        # Obtener el texto limpio separando por espacios
        text = soup.get_text(separator=" ", strip=True)

        return title, text