"""
Pixel Art Transformer - Command Line Interface
===============================================
Convert upscaled pixel art images to their true pixel dimensions.

Usage:
    python pixel_art_transformer.py <input_image> [options]
    
Examples:
    python pixel_art_transformer.py sprite.png
    python pixel_art_transformer.py sprite.png --grid-size 16
    python pixel_art_transformer.py sprite.png --show-grid --output result.png
"""

from __future__ import annotations

import argparse
import sys
import logging
from pathlib import Path

from PIL import Image

from config import GRID_DETECTION, FILE, setup_logging
from core import (
    detect_pixel_size, 
    transform_to_real_pixels, 
    create_grid_visualization
)
from core.exceptions import InvalidImageError, GridDetectionError


# Module logger
logger = setup_logging(logging.INFO)


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description='Convert pixel art to its true pixel dimensions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python pixel_art_transformer.py sprite.png
  python pixel_art_transformer.py sprite.png --grid-size 16
  python pixel_art_transformer.py sprite.png --show-grid --output result.png
        '''
    )
    
    parser.add_argument(
        'input', 
        help='Input image file (pixel art)'
    )
    parser.add_argument(
        '--grid-size', '-g', 
        type=int, 
        default=0,
        help='Grid/pixel size (0 = auto-detect)'
    )
    parser.add_argument(
        '--show-grid', '-s', 
        action='store_true',
        help='Save grid visualization overlay'
    )
    parser.add_argument(
        '--output', '-o', 
        type=str, 
        default='',
        help=f'Output filename (default: <input>{FILE.output_suffix}.png)'
    )
    parser.add_argument(
        '--no-center-markers', 
        action='store_true',
        help='Do not show center markers in grid visualization'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    return parser.parse_args()


def main() -> int:
    """
    Main entry point for the CLI.
    
    Returns:
        Exit code (0 for success, non-zero for error).
    """
    args = parse_arguments()
    
    if args.verbose:
        setup_logging(logging.DEBUG)
    
    # Validate input file
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error("File not found: %s", args.input)
        print(f"❌ Error: No se encuentra el archivo '{args.input}'")
        return 1
    
    # Load image
    print(f"📷 Cargando imagen: {input_path}")
    try:
        image = Image.open(input_path)
        logger.info("Loaded image: %s (%dx%d, mode=%s)", 
                   input_path.name, image.width, image.height, image.mode)
    except Exception as e:
        logger.exception("Failed to load image")
        raise InvalidImageError(str(input_path), str(e))
    
    print(f"   Dimensiones originales: {image.width}x{image.height}")
    print(f"   Modo de color: {image.mode}")
    
    # Detect or use specified grid size
    if args.grid_size > 0:
        cell_size = args.grid_size
        print(f"📐 Usando tamaño de grid especificado: {cell_size}x{cell_size}")
    else:
        print("🔍 Auto-detectando tamaño del pixel...")
        cell_size = detect_pixel_size(image)
        print(f"   Tamaño detectado: {cell_size}x{cell_size}")
    
    if cell_size < GRID_DETECTION.min_pixel_size:
        print("⚠️  No se detectó un patrón de pixel art.")
        print("   La imagen parece ser ya pixel-perfect.")
        print("   Usa --grid-size para especificar manualmente el tamaño.")
        return 0
    
    # Calculate output dimensions
    new_width = image.width // cell_size
    new_height = image.height // cell_size
    print(f"📊 Dimensiones del resultado: {new_width}x{new_height}")
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.parent / f"{input_path.stem}{FILE.output_suffix}.png"
    
    # Transform image
    print("✨ Transformando a pixel art real...")
    try:
        result = transform_to_real_pixels(image, cell_size)
    except Exception as e:
        logger.exception("Transformation failed")
        print(f"❌ Error durante la transformación: {e}")
        return 1
    
    # Save result
    try:
        result.save(output_path, FILE.output_format)
        logger.info("Saved result: %s", output_path)
        print(f"💾 Imagen guardada: {output_path}")
    except Exception as e:
        logger.exception("Failed to save result")
        print(f"❌ Error al guardar: {e}")
        return 1
    
    # Save grid visualization if requested
    if args.show_grid:
        grid_path = input_path.parent / f"{input_path.stem}{FILE.grid_suffix}.png"
        print("📏 Generando visualización del grid...")
        
        try:
            grid_viz = create_grid_visualization(
                image, 
                cell_size,
                center_marker=not args.no_center_markers
            )
            grid_viz.save(grid_path, FILE.output_format)
            logger.info("Saved grid visualization: %s", grid_path)
            print(f"💾 Grid guardado: {grid_path}")
        except Exception as e:
            logger.exception("Failed to save grid visualization")
            print(f"⚠️  Error al guardar visualización del grid: {e}")
    
    # Summary
    print("✅ ¡Transformación completada!")
    print(f"   Reducción: {image.width}x{image.height} → {new_width}x{new_height}")
    print(f"   Factor: {cell_size}x")
    
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⚠️  Operación cancelada")
        sys.exit(130)
    except Exception as e:
        logger.exception("Fatal error")
        print(f"❌ Error fatal: {e}")
        sys.exit(1)
