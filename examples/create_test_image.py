"""
Script de prueba para generar una imagen pixel art de ejemplo
y demostrar el funcionamiento del transformador.
"""

from PIL import Image
import os

# Crear un pixel art simple de 8x8 (un corazón)
pixel_art = [
    [0, 1, 1, 0, 0, 1, 1, 0],
    [1, 2, 2, 1, 1, 2, 2, 1],
    [1, 2, 2, 2, 2, 2, 2, 1],
    [1, 2, 2, 2, 2, 2, 2, 1],
    [0, 1, 2, 2, 2, 2, 1, 0],
    [0, 0, 1, 2, 2, 1, 0, 0],
    [0, 0, 0, 1, 1, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
]

# Paleta de colores
palette = {
    0: (40, 40, 60),      # Fondo oscuro
    1: (180, 50, 80),     # Borde rojo oscuro
    2: (255, 80, 120),    # Rojo claro del corazón
}

# Tamaño del "pixel" escalado
PIXEL_SIZE = 16

# Dimensiones
art_width = len(pixel_art[0])
art_height = len(pixel_art)
scaled_width = art_width * PIXEL_SIZE
scaled_height = art_height * PIXEL_SIZE

# Crear imagen escalada (simulando pixel art redimensionado)
scaled_image = Image.new('RGB', (scaled_width, scaled_height))

for y, row in enumerate(pixel_art):
    for x, color_idx in enumerate(row):
        color = palette[color_idx]
        # Rellenar el bloque de PIXEL_SIZE x PIXEL_SIZE
        for py in range(PIXEL_SIZE):
            for px in range(PIXEL_SIZE):
                scaled_image.putpixel(
                    (x * PIXEL_SIZE + px, y * PIXEL_SIZE + py),
                    color
                )

# Guardar imagen de prueba
output_path = os.path.join(os.path.dirname(__file__), 'test_heart.png')
scaled_image.save(output_path, 'PNG')
print(f"✅ Imagen de prueba creada: {output_path}")
print(f"   Dimensiones: {scaled_width}x{scaled_height} (pixel art {art_width}x{art_height} escalado {PIXEL_SIZE}x)")
print(f"\nAhora ejecuta:")
print(f"   python pixel_art_transformer.py test_heart.png --show-grid")
