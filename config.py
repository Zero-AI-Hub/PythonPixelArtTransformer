"""
Pixel Art Transformer - Configuration
======================================
Centralized configuration for all constants, thresholds, and settings.
"""

from dataclasses import dataclass
from typing import Tuple
import logging


# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = logging.INFO


def setup_logging(level: int = LOG_LEVEL) -> logging.Logger:
    """Configure and return the application logger."""
    logging.basicConfig(format=LOG_FORMAT, level=level)
    return logging.getLogger("PixelArtTransformer")


# =============================================================================
# UI COLORS
# =============================================================================

@dataclass(frozen=True)
class UIColors:
    """Color scheme for the application UI."""
    background: str = "#1a1a2e"
    foreground: str = "#eaeaea"
    accent: str = "#e94560"
    accent_green: str = "#00ff88"
    secondary_bg: str = "#16213e"
    canvas_bg: str = "#0f0f23"
    muted: str = "#888888"
    
    # Grid overlay colors (RGBA)
    grid_line: Tuple[int, int, int, int] = (255, 50, 80, 150)
    center_marker: Tuple[int, int, int, int] = (50, 255, 100, 200)
    excluded_marker: Tuple[int, int, int, int] = (255, 100, 100, 200)
    selection_rect: str = "#e94560"
    region_outline: str = "#00ff88"


UI_COLORS = UIColors()


# =============================================================================
# ZOOM SETTINGS
# =============================================================================

@dataclass(frozen=True)
class ZoomSettings:
    """Zoom configuration for canvases."""
    default: float = 1.0
    min_level: float = 0.1
    max_level_region: float = 10.0
    max_level_editor: float = 20.0
    max_level_initial: float = 2.0
    max_level_initial_editor: float = 4.0
    zoom_factor_in: float = 1.2
    zoom_factor_out: float = 0.8


ZOOM = ZoomSettings()


# =============================================================================
# GRID DETECTION
# =============================================================================

@dataclass(frozen=True)
class GridDetectionSettings:
    """Settings for automatic grid size detection."""
    # Common pixel art sizes, ordered largest to smallest
    common_sizes: Tuple[int, ...] = (64, 48, 32, 24, 16, 12, 10, 8, 6, 5, 4, 3, 2)
    max_check_size: int = 128
    max_samples: int = 100
    uniformity_threshold: float = 0.95  # Percentage of uniform blocks required
    uniformity_threshold_gui: float = 0.90  # Slightly lower for GUI preview
    min_pixel_size: int = 2


GRID_DETECTION = GridDetectionSettings()


# =============================================================================
# REGION SELECTION
# =============================================================================

@dataclass(frozen=True)
class RegionSettings:
    """Settings for region selection."""
    min_region_size: int = 10  # Minimum pixels for a valid region
    default_grid_size: int = 32
    max_grid_size: int = 64
    min_grid_size: int = 2
    offset_range: Tuple[int, int] = (-32, 32)
    tolerance_range: Tuple[int, int] = (0, 50)
    default_tolerance: int = 10


REGION = RegionSettings()


# =============================================================================
# COLOR PROCESSING
# =============================================================================

@dataclass(frozen=True)
class ColorSettings:
    """Settings for color processing."""
    bit_depth_options: Tuple[Tuple[str, int], ...] = (
        ("8-bit", 8),
        ("6-bit", 6),
        ("4-bit", 4),
        ("3-bit", 3),
    )
    default_bit_depth: int = 8
    max_excluded_colors: int = 2


COLOR = ColorSettings()


# =============================================================================
# WINDOW SETTINGS
# =============================================================================

@dataclass(frozen=True)
class WindowSettings:
    """Window configuration."""
    default_geometry: str = "1280x720"
    min_width: int = 1024
    min_height: int = 600
    title: str = "🎨 Pixel Art Transformer v6"
    min_canvas_size: int = 10  # Minimum canvas dimension for calculations


WINDOW = WindowSettings()


# =============================================================================
# FILE SETTINGS
# =============================================================================

@dataclass(frozen=True)
class FileSettings:
    """File handling configuration."""
    supported_formats: Tuple[Tuple[str, str], ...] = (
        ("Imágenes", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
        ("Todos", "*.*"),
    )
    output_format: str = "PNG"
    output_suffix: str = "_real"
    grid_suffix: str = "_grid"
    region_suffix: str = "_region"
    
    # Standard pixel art size presets (name, size)
    output_size_presets: Tuple[Tuple[str, int], ...] = (
        ("Original", 0),  # 0 means keep original size
        ("8×8", 8),
        ("16×16", 16),
        ("24×24", 24),
        ("32×32", 32),
        ("48×48", 48),
        ("64×64", 64),
        ("96×96", 96),
        ("128×128", 128),
        ("256×256", 256),
    )


FILE = FileSettings()


# =============================================================================
# GRID EDITOR SETTINGS
# =============================================================================

@dataclass(frozen=True)
class GridEditorSettings:
    """Settings for the advanced grid editor."""
    # Distance in screen pixels to detect line for dragging
    line_grab_distance: int = 8
    
    # Minimum cell size in image pixels
    min_cell_size: int = 2
    
    # Colors for grid lines (hex for canvas)
    line_color_normal: str = "#ff3250"
    line_color_hover: str = "#ffff00"
    line_color_dragging: str = "#00ff88"
    
    # Colors for cell overlay (RGBA)
    cell_excluded_overlay: Tuple[int, int, int, int] = (255, 80, 80, 120)
    cell_included_overlay: Tuple[int, int, int, int] = (80, 255, 80, 80)
    cell_hover_overlay: Tuple[int, int, int, int] = (255, 255, 100, 60)
    
    # Line width
    line_width_normal: int = 1
    line_width_hover: int = 3


GRID_EDITOR = GridEditorSettings()
