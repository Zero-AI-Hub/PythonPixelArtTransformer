"""
Pixel Art Transformer
=====================
Convierte imágenes de pixel art a su forma "real" (1 pixel por pixel),
tomando el color del centro de cada celda del grid original.

Uso:
    python pixel_art_transformer.py <imagen_entrada> [--grid-size N] [--show-grid] [--output nombre_salida.png]
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
    import numpy as np
except ImportError:
    print("Error: Se requieren las librerías Pillow y numpy.")
    print("Instálalas con: pip install Pillow numpy")
    sys.exit(1)


def detect_pixel_size(image: Image.Image, max_check: int = 128) -> int:
    """
    Detecta automáticamente el tamaño del pixel art analizando patrones repetidos.
    Busca el mayor tamaño de bloque uniforme, priorizando tamaños comunes.
    """
    img_array = np.array(image)
    width, height = image.size
    
    # Tamaños comunes en pixel art, ordenados de mayor a menor
    common_sizes = [64, 48, 32, 24, 16, 12, 10, 8, 6, 5, 4, 3, 2]
    # Añadir otros tamaños que dividan la imagen
    all_sizes = []
    for size in range(max_check, 1, -1):
        if width % size == 0 and height % size == 0:
            all_sizes.append(size)
    
    # Priorizar tamaños comunes
    sizes_to_check = []
    for s in common_sizes:
        if s in all_sizes:
            sizes_to_check.append(s)
    for s in all_sizes:
        if s not in sizes_to_check:
            sizes_to_check.append(s)
    
    best_size = 1
    
    for size in sizes_to_check:
        # Verificar si TODOS los bloques son uniformes
        is_uniform = True
        blocks_x = width // size
        blocks_y = height // size
        
        # Revisar todos los bloques (o una muestra si hay muchos)
        max_samples = min(100, blocks_x * blocks_y)
        step = max(1, (blocks_x * blocks_y) // max_samples)
        
        sample_count = 0
        uniform_count = 0
        
        for i in range(0, blocks_x * blocks_y, step):
            bx = (i % blocks_x) * size
            by = (i // blocks_x) * size
            
            block = img_array[by:by+size, bx:bx+size]
            
            # El bloque es uniforme si todos los píxeles son iguales
            if len(block.shape) == 3:
                # Imagen a color
                first_pixel = block[0, 0]
                if np.all(block == first_pixel):
                    uniform_count += 1
            else:
                # Imagen en escala de grises
                if np.all(block == block[0, 0]):
                    uniform_count += 1
            
            sample_count += 1
        
        # Si al menos 95% de los bloques son uniformes, es el tamaño correcto
        if sample_count > 0 and uniform_count / sample_count >= 0.95:
            best_size = size
            break
    
    return best_size


def get_center_color(image: Image.Image, x: int, y: int, cell_size: int) -> tuple:
    """
    Obtiene el color del centro de una celda del grid.
    """
    center_x = x + cell_size // 2
    center_y = y + cell_size // 2
    
    # Asegurarse de que estamos dentro de los límites
    center_x = min(center_x, image.width - 1)
    center_y = min(center_y, image.height - 1)
    
    return image.getpixel((center_x, center_y))


def transform_to_real_pixels(image: Image.Image, cell_size: int) -> Image.Image:
    """
    Transforma la imagen tomando el color del centro de cada celda
    y creando una imagen donde cada celda se convierte en 1 pixel.
    """
    width, height = image.size
    new_width = width // cell_size
    new_height = height // cell_size
    
    # Crear nueva imagen
    mode = image.mode
    if mode == 'P':  # Palette mode
        image = image.convert('RGBA')
        mode = 'RGBA'
    
    new_image = Image.new(mode, (new_width, new_height))
    
    for y in range(new_height):
        for x in range(new_width):
            orig_x = x * cell_size
            orig_y = y * cell_size
            color = get_center_color(image, orig_x, orig_y, cell_size)
            new_image.putpixel((x, y), color)
    
    return new_image


def create_grid_visualization(image: Image.Image, cell_size: int, 
                             grid_color: tuple = (255, 0, 0, 128),
                             center_marker: bool = True) -> Image.Image:
    """
    Crea una visualización del grid sobre la imagen original,
    mostrando las celdas y opcionalmente los puntos centrales que se muestrean.
    """
    # Crear copia con canal alpha
    if image.mode != 'RGBA':
        viz_image = image.convert('RGBA')
    else:
        viz_image = image.copy()
    
    # Crear overlay para el grid
    overlay = Image.new('RGBA', viz_image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    width, height = image.size
    
    # Dibujar líneas verticales
    for x in range(0, width + 1, cell_size):
        draw.line([(x, 0), (x, height)], fill=grid_color, width=1)
    
    # Dibujar líneas horizontales
    for y in range(0, height + 1, cell_size):
        draw.line([(0, y), (width, y)], fill=grid_color, width=1)
    
    # Marcar los centros de cada celda
    if center_marker:
        center_color = (0, 255, 0, 200)  # Verde para los centros
        marker_size = max(1, cell_size // 8)
        
        for y in range(0, height, cell_size):
            for x in range(0, width, cell_size):
                cx = x + cell_size // 2
                cy = y + cell_size // 2
                if cx < width and cy < height:
                    draw.ellipse(
                        [(cx - marker_size, cy - marker_size), 
                         (cx + marker_size, cy + marker_size)],
                        fill=center_color
                    )
    
    # Combinar overlay con imagen
    viz_image = Image.alpha_composite(viz_image, overlay)
    
    return viz_image


def main():
    parser = argparse.ArgumentParser(
        description='Convierte pixel art a su forma real (1 pixel por pixel)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Ejemplos:
  python pixel_art_transformer.py sprite.png
  python pixel_art_transformer.py sprite.png --grid-size 16
  python pixel_art_transformer.py sprite.png --show-grid --output resultado.png
        '''
    )
    
    parser.add_argument('input', help='Imagen de entrada (pixel art)')
    parser.add_argument('--grid-size', '-g', type=int, default=0,
                       help='Tamaño del grid/pixel (0 = auto-detectar)')
    parser.add_argument('--show-grid', '-s', action='store_true',
                       help='Guardar visualización del grid')
    parser.add_argument('--output', '-o', type=str, default='',
                       help='Nombre del archivo de salida (default: <input>_real.png)')
    parser.add_argument('--no-center-markers', action='store_true',
                       help='No mostrar marcadores en los centros del grid')
    
    args = parser.parse_args()
    
    # Cargar imagen
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: No se encuentra el archivo '{args.input}'")
        sys.exit(1)
    
    print(f"📷 Cargando imagen: {input_path}")
    image = Image.open(input_path)
    print(f"   Dimensiones originales: {image.size[0]}x{image.size[1]}")
    print(f"   Modo de color: {image.mode}")
    
    # Detectar o usar el tamaño del grid
    if args.grid_size > 0:
        cell_size = args.grid_size
        print(f"📐 Usando tamaño de grid especificado: {cell_size}x{cell_size}")
    else:
        print("🔍 Auto-detectando tamaño del pixel...")
        cell_size = detect_pixel_size(image)
        print(f"   Tamaño detectado: {cell_size}x{cell_size}")
    
    if cell_size < 2:
        print("⚠️  No se detectó un patrón de pixel art. La imagen parece ser ya pixel-perfect.")
        print("   Usa --grid-size para especificar manualmente el tamaño.")
        sys.exit(0)
    
    # Calcular dimensiones finales
    new_width = image.size[0] // cell_size
    new_height = image.size[1] // cell_size
    print(f"📊 Dimensiones del resultado: {new_width}x{new_height}")
    
    # Determinar nombre de salida
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.parent / f"{input_path.stem}_real.png"
    
    # Transformar imagen
    print("✨ Transformando a pixel art real...")
    result = transform_to_real_pixels(image, cell_size)
    
    # Guardar resultado
    result.save(output_path, 'PNG')
    print(f"💾 Imagen guardada: {output_path}")
    
    # Guardar visualización del grid si se solicita
    if args.show_grid:
        grid_path = input_path.parent / f"{input_path.stem}_grid.png"
        print("📏 Generando visualización del grid...")
        grid_viz = create_grid_visualization(
            image, cell_size, 
            center_marker=not args.no_center_markers
        )
        grid_viz.save(grid_path, 'PNG')
        print(f"💾 Grid guardado: {grid_path}")
    
    print("✅ ¡Transformación completada!")
    print(f"   Reducción: {image.size[0]}x{image.size[1]} → {new_width}x{new_height}")
    print(f"   Factor: {cell_size}x")


if __name__ == '__main__':
    main()
