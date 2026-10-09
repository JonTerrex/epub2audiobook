import re
import ftfy
from num2words import num2words


class TextCleaner:
    """Clase encargada de la limpieza profunda, corrección Unicode

    y normalización de texto para síntesis de voz en español.
    """

    def __init__(self, lang: str = "es"):
        self.lang = lang

        # Mapeo de símbolos comunes a palabras
        self.symbol_replacements = {
            "%": " por ciento",
            "&": " y ",
            "$": " dólares ",
            "€": " euros ",
            "@": " arroba ",
            "#": " número ",
            "=": " igual a ",
            "+": " más ",
        }

        # Abreviaturas habituales en castellano
        self.abbreviations = {
            r"\bDr\.\b": "Doctor",
            r"\bDra\.\b": "Doctora",
            r"\bSr\.\b": "Señor",
            r"\bSra\.\b": "Señora",
            r"\bSrta\.\b": "Señorita",
            r"\bpág\.\b": "página",
            r"\bpágs\.\b": "páginas",
            r"\bej\.\b": "ejemplo",
            r"\bEE\.UU\.\b": "Estados Unidos",
        }

    def clean(self, text: str) -> str:
        """Aplica el pipeline completo de limpieza al texto de entrada."""
        if not text:
            return ""

        # 1. Reparar problemas de codificación Unicode (mojibake)
        text = ftfy.fix_text(text)

        # 2. Eliminar referencias a notas de pie o corchetes [1], [nota 2]
        text = re.sub(r"\[\s*(?:nota\s*)?\d+\s*\]", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\(\s*pág\.\s*\d+\s*\)", "", text, flags=re.IGNORECASE)

        # 3. Normalizar comillas y rayas de diálogo
        text = self._normalize_punctuation(text)

        # 4. Expandir abreviaturas
        for pattern, replacement in self.abbreviations.items():
            text = re.sub(pattern, replacement, text)

        # 5. Sustituir símbolos por palabras
        for symbol, word in self.symbol_replacements.items():
            text = text.replace(symbol, word)

        # 6. Convertir números a texto (ej. 1984 -> mil novecientos ochenta y cuatro)
        text = self._convert_numbers_to_words(text)

        # 7. Colapsar espacios en blanco múltiples
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def _normalize_punctuation(self, text: str) -> str:
        """Estandariza rayas de diálogo, comillas y guiones."""
        # Convertir comillas raras a comillas dobles estándar
        text = re.sub(r"[«»“”„]", '"', text)

        # Normalizar rayas de diálogo largas a un guión simple con espacios
        text = re.sub(r"[—–]", " - ", text)

        return text

    def _convert_numbers_to_words(self, text: str) -> str:
        """Encuentra secuencias numéricas y las transforma a su equivalente en palabras."""

        def replacer(match: re.Match) -> str:
            number_str = match.group(0)
            try:
                # Convertir entero a palabras en español
                return num2words(int(number_str), lang=self.lang)
            except ValueError:
                return number_str

        # Buscar dígitos aislados de hasta 6 cifras (evita modificar IDs largos)
        return re.sub(r"\b\d{1,6}\b", replacer, text)