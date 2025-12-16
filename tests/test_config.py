"""
Tests for configuration module.
"""

import pytest

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    UI_COLORS,
    ZOOM,
    GRID_DETECTION,
    REGION,
    COLOR,
    WINDOW,
    FILE,
    setup_logging,
)


class TestUIColors:
    """Tests for UI color configuration."""
    
    def test_colors_are_hex_strings(self):
        """UI colors should be valid hex strings."""
        for color in [
            UI_COLORS.background,
            UI_COLORS.foreground,
            UI_COLORS.accent,
        ]:
            assert color.startswith('#')
            assert len(color) == 7  # #RRGGBB
    
    def test_rgba_colors_are_tuples(self):
        """RGBA colors should be 4-element tuples."""
        assert len(UI_COLORS.grid_line) == 4
        assert len(UI_COLORS.center_marker) == 4
        assert len(UI_COLORS.excluded_marker) == 4
    
    def test_rgba_values_in_range(self):
        """RGBA values should be 0-255."""
        for rgba in [UI_COLORS.grid_line, UI_COLORS.center_marker]:
            for value in rgba:
                assert 0 <= value <= 255


class TestZoomSettings:
    """Tests for zoom configuration."""
    
    def test_zoom_limits_valid(self):
        """Zoom limits should be positive and ordered correctly."""
        assert ZOOM.min_level > 0
        assert ZOOM.min_level < ZOOM.max_level_region
        assert ZOOM.min_level < ZOOM.max_level_editor
    
    def test_zoom_factors_valid(self):
        """Zoom factors should be sensible."""
        assert ZOOM.zoom_factor_in > 1.0  # Zoom in increases
        assert ZOOM.zoom_factor_out < 1.0  # Zoom out decreases
        assert ZOOM.zoom_factor_out > 0  # But not negative


class TestGridDetectionSettings:
    """Tests for grid detection configuration."""
    
    def test_common_sizes_sorted(self):
        """Common sizes should be sorted largest first."""
        sizes = list(GRID_DETECTION.common_sizes)
        assert sizes == sorted(sizes, reverse=True)
    
    def test_thresholds_valid(self):
        """Uniformity thresholds should be 0-1."""
        assert 0 < GRID_DETECTION.uniformity_threshold <= 1
        assert 0 < GRID_DETECTION.uniformity_threshold_gui <= 1
    
    def test_min_pixel_size(self):
        """Minimum pixel size should be at least 2."""
        assert GRID_DETECTION.min_pixel_size >= 2


class TestRegionSettings:
    """Tests for region configuration."""
    
    def test_grid_size_range(self):
        """Grid size range should be valid."""
        assert REGION.min_grid_size > 0
        assert REGION.min_grid_size < REGION.max_grid_size
        assert REGION.min_grid_size <= REGION.default_grid_size <= REGION.max_grid_size
    
    def test_offset_range(self):
        """Offset range should include negative and positive."""
        min_off, max_off = REGION.offset_range
        assert min_off < 0
        assert max_off > 0
    
    def test_tolerance_range(self):
        """Tolerance range should start at 0."""
        min_tol, max_tol = REGION.tolerance_range
        assert min_tol == 0
        assert max_tol > 0
        assert min_tol <= REGION.default_tolerance <= max_tol


class TestColorSettings:
    """Tests for color configuration."""
    
    def test_bit_depth_options_valid(self):
        """Bit depth options should be valid."""
        for name, bits in COLOR.bit_depth_options:
            assert isinstance(name, str)
            assert 1 <= bits <= 8
    
    def test_default_in_options(self):
        """Default bit depth should be in options."""
        bits = [b for _, b in COLOR.bit_depth_options]
        assert COLOR.default_bit_depth in bits


class TestWindowSettings:
    """Tests for window configuration."""
    
    def test_geometry_format(self):
        """Geometry should be WxH format."""
        assert 'x' in WINDOW.default_geometry
        w, h = WINDOW.default_geometry.split('x')
        assert int(w) > 0
        assert int(h) > 0
    
    def test_min_size_valid(self):
        """Minimum size should be positive."""
        assert WINDOW.min_width > 0
        assert WINDOW.min_height > 0


class TestFileSettings:
    """Tests for file configuration."""
    
    def test_supported_formats_not_empty(self):
        """Should have at least one supported format."""
        assert len(FILE.supported_formats) > 0
    
    def test_output_format_valid(self):
        """Output format should be a valid image format."""
        assert FILE.output_format in ['PNG', 'JPEG', 'GIF', 'BMP', 'WEBP']


class TestLogging:
    """Tests for logging setup."""
    
    def test_setup_returns_logger(self):
        """setup_logging should return a logger."""
        import logging
        logger = setup_logging()
        assert isinstance(logger, logging.Logger)
    
    def test_logger_has_correct_name(self):
        """Logger should have expected name."""
        logger = setup_logging()
        assert logger.name == "PixelArtTransformer"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
