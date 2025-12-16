"""
Pixel Art Transformer - Core Processing Logic
==============================================
Unified image processing functions with type hints and documentation.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
from PIL import Image, ImageDraw

if TYPE_CHECKING:
    from numpy.typing import NDArray

from config import GRID_DETECTION, setup_logging

# Module logger
logger = setup_logging()


# =============================================================================
# TYPE ALIASES
# =============================================================================

Color = tuple[int, int, int]
ColorRGBA = tuple[int, int, int, int]
Coords = tuple[int, int, int, int]


# =============================================================================
# COLOR PROCESSING
# =============================================================================

def reduce_color(color: Color | ColorRGBA, bits: int) -> Color:
    """
    Reduce a color to a specified bit depth per channel.
    
    This quantizes each color channel to fewer levels, simulating
    limited color palettes common in retro games.
    
    Args:
        color: RGB or RGBA tuple (0-255 per channel).
        bits: Target bit depth (1-8). 8 returns unchanged, lower values quantize.
    
    Returns:
        Quantized RGB tuple.
    
    Examples:
        >>> reduce_color((200, 100, 50), 4)  # 16 levels per channel
        (200, 104, 56)
        >>> reduce_color((200, 100, 50), 8)  # No change
        (200, 100, 50)
    """
    if bits >= 8:
        return color[:3]  # type: ignore
    
    levels = 2 ** bits
    factor = 256 // levels
    
    return tuple(
        min(255, (c // factor) * factor + factor // 2) 
        for c in color[:3]
    )  # type: ignore


def colors_similar(c1: Color, c2: Color, tolerance: int) -> bool:
    """
    Check if two colors are similar within a tolerance.
    
    Uses Manhattan distance (sum of absolute differences) per channel.
    
    Args:
        c1: First RGB color.
        c2: Second RGB color.
        tolerance: Maximum difference allowed per channel.
    
    Returns:
        True if all channels are within tolerance.
    
    Examples:
        >>> colors_similar((100, 100, 100), (105, 95, 100), 10)
        True
        >>> colors_similar((100, 100, 100), (120, 100, 100), 10)
        False
    """
    return all(abs(a - b) <= tolerance for a, b in zip(c1, c2))


def get_center_color(image: Image.Image, x: int, y: int, cell_size: int) -> ColorRGBA:
    """
    Get the color at the center of a grid cell.
    
    Args:
        image: PIL Image to sample from.
        x: Left coordinate of the cell.
        y: Top coordinate of the cell.
        cell_size: Size of the grid cell.
    
    Returns:
        RGBA color tuple at the cell center.
    """
    center_x = min(x + cell_size // 2, image.width - 1)
    center_y = min(y + cell_size // 2, image.height - 1)
    
    color = image.getpixel((center_x, center_y))
    
    # Ensure RGBA format
    if len(color) == 3:
        return color + (255,)
    return color


# =============================================================================
# GRID DETECTION
# =============================================================================

def detect_pixel_size(
    image: Image.Image, 
    max_check: int = GRID_DETECTION.max_check_size,
    threshold: float = GRID_DETECTION.uniformity_threshold
) -> int:
    """
    Auto-detect the pixel/grid size of upscaled pixel art.
    
    Analyzes the image for repeating uniform blocks. Prioritizes common
    pixel art sizes (16, 32, etc.) and finds the largest size where
    most blocks are uniform (single color).
    
    Args:
        image: PIL Image to analyze.
        max_check: Maximum grid size to check.
        threshold: Minimum percentage (0-1) of uniform blocks required.
    
    Returns:
        Detected pixel size, or 1 if no pattern found.
    
    Raises:
        ValueError: If image is too small to analyze.
    """
    img_array = np.array(image.convert('RGB'))
    width, height = image.size
    
    if width < 2 or height < 2:
        logger.warning("Image too small for grid detection: %dx%d", width, height)
        return 1
    
    # Build list of sizes to check, prioritizing common ones
    all_sizes: list[int] = []
    for size in range(max_check, 1, -1):
        if width % size == 0 and height % size == 0:
            all_sizes.append(size)
    
    # Prioritize common pixel art sizes
    sizes_to_check: list[int] = []
    for s in GRID_DETECTION.common_sizes:
        if s in all_sizes:
            sizes_to_check.append(s)
    for s in all_sizes:
        if s not in sizes_to_check:
            sizes_to_check.append(s)
    
    logger.debug("Checking grid sizes: %s", sizes_to_check[:10])
    
    best_size = 1
    
    for size in sizes_to_check:
        blocks_x = width // size
        blocks_y = height // size
        total_blocks = blocks_x * blocks_y
        
        # Sample blocks (up to max_samples)
        max_samples = min(GRID_DETECTION.max_samples, total_blocks)
        step = max(1, total_blocks // max_samples)
        
        sample_count = 0
        uniform_count = 0
        
        for i in range(0, total_blocks, step):
            bx = (i % blocks_x) * size
            by = (i // blocks_x) * size
            
            block = img_array[by:by+size, bx:bx+size]
            
            # Check if block is uniform (all pixels same color)
            first_pixel = block[0, 0]
            if np.all(block == first_pixel):
                uniform_count += 1
            
            sample_count += 1
        
        # Check if enough blocks are uniform
        if sample_count > 0:
            uniformity = uniform_count / sample_count
            logger.debug("Size %d: %.1f%% uniform", size, uniformity * 100)
            
            if uniformity >= threshold:
                best_size = size
                break
    
    logger.info("Detected pixel size: %d", best_size)
    return best_size


# =============================================================================
# IMAGE TRANSFORMATION
# =============================================================================

def transform_to_real_pixels(
    image: Image.Image, 
    cell_size: int,
    offset_x: int = 0,
    offset_y: int = 0,
    bit_depth: int = 8,
    excluded_colors: list[Color | None] | None = None,
    tolerance: int = 10
) -> Image.Image:
    """
    Transform upscaled pixel art to true pixel dimensions.
    
    Samples the center color of each grid cell and creates a new image
    where each cell becomes one pixel.
    
    Args:
        image: Source image (upscaled pixel art).
        cell_size: Size of each grid cell in pixels.
        offset_x: Horizontal offset for grid alignment.
        offset_y: Vertical offset for grid alignment.
        bit_depth: Color quantization (1-8 bits per channel).
        excluded_colors: Colors to make transparent.
        tolerance: Tolerance for color matching when excluding.
    
    Returns:
        New Image at true pixel dimensions with RGBA mode.
    
    Raises:
        ValueError: If cell_size is invalid.
    """
    if cell_size < 1:
        raise ValueError(f"Invalid cell size: {cell_size}")
    
    width, height = image.size
    
    # Handle palette mode
    if image.mode == 'P':
        image = image.convert('RGBA')
    elif image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # Calculate start positions
    start_x = offset_x if offset_x >= 0 else offset_x % cell_size
    start_y = offset_y if offset_y >= 0 else offset_y % cell_size
    
    # Calculate output dimensions
    new_width = (width - start_x) // cell_size
    new_height = (height - start_y) // cell_size
    
    if new_width < 1 or new_height < 1:
        raise ValueError(f"Result would be empty: {new_width}x{new_height}")
    
    # Create output image
    result = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))
    
    # Prepare excluded colors list
    excluded: list[Color] = [c for c in (excluded_colors or []) if c is not None]
    
    # Process each cell
    for py in range(new_height):
        for px in range(new_width):
            cx = start_x + px * cell_size + cell_size // 2
            cy = start_y + py * cell_size + cell_size // 2
            
            # Ensure within bounds
            cx = min(cx, width - 1)
            cy = min(cy, height - 1)
            
            color = image.getpixel((cx, cy))
            if len(color) == 3:
                color = color + (255,)
            
            # Apply color reduction
            rgb = reduce_color(color[:3], bit_depth)
            
            # Check if excluded
            is_excluded = any(
                colors_similar(rgb, exc, tolerance) 
                for exc in excluded
            )
            
            if is_excluded:
                result.putpixel((px, py), (0, 0, 0, 0))
            else:
                result.putpixel((px, py), rgb + (color[3],))
    
    logger.info(
        "Transformed %dx%d -> %dx%d (cell_size=%d)",
        width, height, new_width, new_height, cell_size
    )
    
    return result


def transform_with_custom_grid(
    image: Image.Image,
    x_lines: list[int],
    y_lines: list[int],
    excluded_cells: set[tuple[int, int]] | None = None,
    bit_depth: int = 8,
    excluded_colors: list[Color | None] | None = None,
    tolerance: int = 10
) -> Image.Image:
    """
    Transform image using custom grid line positions.
    
    This supports non-uniform grids where each cell can have a different size.
    The center of each cell is sampled to create the output pixel.
    
    Args:
        image: Source image.
        x_lines: X positions of vertical grid lines (including edges).
        y_lines: Y positions of horizontal grid lines (including edges).
        excluded_cells: Set of (col, row) cells to make transparent.
        bit_depth: Color quantization (1-8 bits per channel).
        excluded_colors: Colors to make transparent.
        tolerance: Tolerance for color matching when excluding.
    
    Returns:
        New Image at true pixel dimensions with RGBA mode.
    
    Raises:
        ValueError: If grid is invalid.
    """
    if len(x_lines) < 2 or len(y_lines) < 2:
        raise ValueError("Grid must have at least 2 lines in each direction")
    
    num_cols = len(x_lines) - 1
    num_rows = len(y_lines) - 1
    
    if num_cols < 1 or num_rows < 1:
        raise ValueError(f"Grid too small: {num_cols}x{num_rows}")
    
    # Handle palette mode
    if image.mode == 'P':
        image = image.convert('RGBA')
    elif image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    width, height = image.size
    
    # Create output image
    result = Image.new('RGBA', (num_cols, num_rows), (0, 0, 0, 0))
    
    # Prepare excluded colors list
    excluded: list[Color] = [c for c in (excluded_colors or []) if c is not None]
    excluded_cells = excluded_cells or set()
    
    # Process each cell
    for row in range(num_rows):
        for col in range(num_cols):
            # Check if manually excluded
            if (col, row) in excluded_cells:
                result.putpixel((col, row), (0, 0, 0, 0))
                continue
            
            # Calculate cell center
            x1, x2 = x_lines[col], x_lines[col + 1]
            y1, y2 = y_lines[row], y_lines[row + 1]
            
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            
            # Clamp to image bounds
            cx = max(0, min(cx, width - 1))
            cy = max(0, min(cy, height - 1))
            
            color = image.getpixel((cx, cy))
            if len(color) == 3:
                color = color + (255,)
            
            # Apply color reduction
            rgb = reduce_color(color[:3], bit_depth)
            
            # Check if color-excluded
            is_excluded = any(
                colors_similar(rgb, exc, tolerance) 
                for exc in excluded
            )
            
            if is_excluded:
                result.putpixel((col, row), (0, 0, 0, 0))
            else:
                result.putpixel((col, row), rgb + (color[3],))
    
    logger.info(
        "Transformed with custom grid: %dx%d -> %dx%d",
        width, height, num_cols, num_rows
    )
    
    return result


# =============================================================================
# VISUALIZATION
# =============================================================================

def create_grid_visualization(
    image: Image.Image, 
    cell_size: int,
    grid_color: ColorRGBA = (255, 0, 0, 128),
    center_marker: bool = True,
    offset_x: int = 0,
    offset_y: int = 0
) -> Image.Image:
    """
    Create a visualization of the grid overlay on an image.
    
    Draws grid lines and optionally marks the center sampling points.
    
    Args:
        image: Source image.
        cell_size: Size of grid cells.
        grid_color: RGBA color for grid lines.
        center_marker: Whether to draw center sampling points.
        offset_x: Horizontal offset for grid.
        offset_y: Vertical offset for grid.
    
    Returns:
        New RGBA image with grid overlay.
    """
    # Convert to RGBA
    if image.mode != 'RGBA':
        viz_image = image.convert('RGBA')
    else:
        viz_image = image.copy()
    
    # Create overlay
    overlay = Image.new('RGBA', viz_image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    width, height = image.size
    
    # Draw vertical lines
    for x in range(offset_x, width + 1, cell_size):
        if x >= 0:
            draw.line([(x, 0), (x, height)], fill=grid_color, width=1)
    
    # Draw horizontal lines
    for y in range(offset_y, height + 1, cell_size):
        if y >= 0:
            draw.line([(0, y), (width, y)], fill=grid_color, width=1)
    
    # Draw center markers
    if center_marker:
        center_color: ColorRGBA = (0, 255, 0, 200)
        marker_size = max(1, cell_size // 8)
        
        start_x = offset_x if offset_x >= 0 else offset_x % cell_size
        start_y = offset_y if offset_y >= 0 else offset_y % cell_size
        
        for y in range(start_y, height, cell_size):
            for x in range(start_x, width, cell_size):
                cx = x + cell_size // 2
                cy = y + cell_size // 2
                if cx < width and cy < height:
                    draw.ellipse(
                        [(cx - marker_size, cy - marker_size), 
                         (cx + marker_size, cy + marker_size)],
                        fill=center_color
                    )
    
    return Image.alpha_composite(viz_image, overlay)


def draw_grid_overlay(
    image: Image.Image,
    cell_size: int,
    offset_x: int = 0,
    offset_y: int = 0,
    show_grid: bool = True,
    show_centers: bool = True,
    bit_depth: int = 8,
    excluded_colors: list[Color | None] | None = None,
    tolerance: int = 10,
    grid_color: ColorRGBA = (255, 50, 80, 150),
    center_color: ColorRGBA = (50, 255, 100, 200),
    excluded_color: ColorRGBA = (255, 100, 100, 200)
) -> Image.Image:
    """
    Draw a grid overlay with optional center markers and exclusion indicators.
    
    This is used for the GUI preview, showing which pixels will be sampled
    and which will be excluded.
    
    Args:
        image: Source image.
        cell_size: Grid cell size.
        offset_x: Horizontal offset.
        offset_y: Vertical offset.
        show_grid: Whether to draw grid lines.
        show_centers: Whether to draw center markers.
        bit_depth: Bit depth for color reduction preview.
        excluded_colors: Colors that will be made transparent.
        tolerance: Tolerance for color matching.
        grid_color: Color for grid lines.
        center_color: Color for normal center markers.
        excluded_color: Color for excluded center markers.
    
    Returns:
        New RGBA image with overlay.
    """
    # Convert to RGBA
    if image.mode != 'RGBA':
        viz = image.convert('RGBA')
    else:
        viz = image.copy()
    
    overlay = Image.new('RGBA', viz.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    width, height = image.size
    
    # Draw grid lines
    if show_grid:
        for x in range(offset_x, width + 1, cell_size):
            if x >= 0:
                draw.line([(x, 0), (x, height)], fill=grid_color, width=1)
        for y in range(offset_y, height + 1, cell_size):
            if y >= 0:
                draw.line([(0, y), (width, y)], fill=grid_color, width=1)
    
    # Draw center markers
    if show_centers:
        marker_size = max(1, cell_size // 8)
        start_x = offset_x if offset_x >= 0 else offset_x % cell_size
        start_y = offset_y if offset_y >= 0 else offset_y % cell_size
        
        excluded: list[Color] = [c for c in (excluded_colors or []) if c is not None]
        
        for y in range(start_y, height, cell_size):
            for x in range(start_x, width, cell_size):
                cx = x + cell_size // 2
                cy = y + cell_size // 2
                
                if 0 <= cx < width and 0 <= cy < height:
                    pixel = image.getpixel((cx, cy))[:3]
                    reduced = reduce_color(pixel, bit_depth)
                    
                    is_excluded = any(
                        colors_similar(reduced, exc, tolerance)
                        for exc in excluded
                    )
                    
                    if is_excluded:
                        # Draw X for excluded
                        draw.line(
                            [(cx - marker_size, cy - marker_size), 
                             (cx + marker_size, cy + marker_size)],
                            fill=excluded_color, width=2
                        )
                        draw.line(
                            [(cx + marker_size, cy - marker_size), 
                             (cx - marker_size, cy + marker_size)],
                            fill=excluded_color, width=2
                        )
                    else:
                        # Draw circle for included
                        draw.ellipse(
                            [(cx - marker_size, cy - marker_size), 
                             (cx + marker_size, cy + marker_size)],
                            fill=center_color
                        )
    
    return Image.alpha_composite(viz, overlay)
