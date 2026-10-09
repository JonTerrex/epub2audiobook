from epub2audiobook.services.text_processor.text_cleaner import TextCleaner

# Instanciamos el limpiador
cleaner = TextCleaner(lang="es")

# Texto de prueba "sucio" con notas, símbolos, números y abreviaturas
dirty_text = (
    "El Dr. García pagó $150 por el 50% de las acciones en 1984 [1]. "
    "Ver pág. 12 (nota 3) — ¡CanciÃ³n excelente!"
)

# Ejecutamos la limpieza
clean_text = cleaner.clean(dirty_text)

print("--- TEXTO ORIGINAL ---")
print(dirty_text)
print("\n--- TEXTO LIMPIO (PARA TTS) ---")
print(clean_text)