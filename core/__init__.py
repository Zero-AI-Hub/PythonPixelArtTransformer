"""
Pixel Art Transformer - Core Package
=====================================
Core image processing functionality, separated from GUI.
"""

from .transformer import (
    detect_pixel_size,
    transform_to_real_pixels,
    transform_with_custom_grid,
    create_grid_visualization,
    reduce_color,
    colors_similar,
    get_center_color,
    draw_grid_overlay,
)

from .exceptions import (
    PixelArtError,
    InvalidImageError,
    GridDetectionError,
    ProcessingError,
)

__all__ = [
    # Transformer functions
    "detect_pixel_size",
    "transform_to_real_pixels",
    "transform_with_custom_grid",
    "create_grid_visualization",
    "reduce_color",
    "colors_similar",
    "get_center_color",
    "draw_grid_overlay",
    # Exceptions
    "PixelArtError",
    "InvalidImageError",
    "GridDetectionError",
    "ProcessingError",
]
