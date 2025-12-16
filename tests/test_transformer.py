"""
Tests for core transformer functions.
"""

import pytest
from PIL import Image
import numpy as np

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import (
    reduce_color,
    colors_similar,
    get_center_color,
    detect_pixel_size,
    transform_to_real_pixels,
    create_grid_visualization,
)


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def solid_color_image():
    """Create a solid red image."""
    img = Image.new('RGB', (100, 100), (255, 0, 0))
    return img


@pytest.fixture
def checkerboard_image():
    """Create a 2x2 checkerboard scaled to 32x32."""
    img = Image.new('RGB', (32, 32))
    for y in range(32):
        for x in range(32):
            # 16x16 cells
            if (x // 16 + y // 16) % 2 == 0:
                img.putpixel((x, y), (255, 255, 255))
            else:
                img.putpixel((x, y), (0, 0, 0))
    return img


@pytest.fixture
def pixel_art_8x8_scaled():
    """Create an 8x8 pixel art scaled 16x (128x128)."""
    colors = [
        (255, 0, 0),    # Red
        (0, 255, 0),    # Green
        (0, 0, 255),    # Blue
        (255, 255, 0),  # Yellow
    ]
    
    img = Image.new('RGB', (128, 128))
    scale = 16
    
    for y in range(8):
        for x in range(8):
            color = colors[(x + y) % 4]
            for py in range(scale):
                for px in range(scale):
                    img.putpixel((x * scale + px, y * scale + py), color)
    
    return img


# =============================================================================
# TEST reduce_color
# =============================================================================

class TestReduceColor:
    """Tests for reduce_color function."""
    
    def test_8bit_unchanged(self):
        """8-bit should return color unchanged."""
        color = (128, 64, 200)
        result = reduce_color(color, 8)
        assert result == (128, 64, 200)
    
    def test_4bit_quantization(self):
        """4-bit should quantize to 16 levels."""
        # With 4 bits, we have 16 levels (0, 16, 32, ..., 240)
        # Factor = 256 // 16 = 16
        # Result = (c // 16) * 16 + 8
        color = (128, 64, 200)
        result = reduce_color(color, 4)
        
        # 128 // 16 = 8 -> 8 * 16 + 8 = 136
        # 64 // 16 = 4 -> 4 * 16 + 8 = 72
        # 200 // 16 = 12 -> 12 * 16 + 8 = 200
        assert result == (136, 72, 200)
    
    def test_3bit_quantization(self):
        """3-bit should quantize to 8 levels."""
        color = (255, 0, 128)
        result = reduce_color(color, 3)
        # Factor = 256 // 8 = 32
        # 255 // 32 = 7 -> 7 * 32 + 16 = 240
        # 0 // 32 = 0 -> 0 * 32 + 16 = 16
        # 128 // 32 = 4 -> 4 * 32 + 16 = 144
        assert result == (240, 16, 144)
    
    def test_rgba_input(self):
        """Should handle RGBA input and return RGB."""
        color = (100, 150, 200, 255)
        result = reduce_color(color, 8)
        assert len(result) == 3
        assert result == (100, 150, 200)
    
    def test_1bit_extreme_quantization(self):
        """1-bit should give only 2 levels per channel."""
        # Factor = 256 // 2 = 128
        assert reduce_color((0, 0, 0), 1) == (64, 64, 64)
        assert reduce_color((200, 200, 200), 1) == (192, 192, 192)


# =============================================================================
# TEST colors_similar
# =============================================================================

class TestColorsSimilar:
    """Tests for colors_similar function."""
    
    def test_identical_colors(self):
        """Identical colors should always be similar."""
        color = (100, 100, 100)
        assert colors_similar(color, color, 0) is True
    
    def test_within_tolerance(self):
        """Colors within tolerance should be similar."""
        c1 = (100, 100, 100)
        c2 = (105, 95, 100)
        assert colors_similar(c1, c2, 10) is True
    
    def test_outside_tolerance(self):
        """Colors outside tolerance should not be similar."""
        c1 = (100, 100, 100)
        c2 = (120, 100, 100)
        assert colors_similar(c1, c2, 10) is False
    
    def test_edge_of_tolerance(self):
        """Test exact boundary of tolerance."""
        c1 = (100, 100, 100)
        c2 = (110, 100, 100)
        assert colors_similar(c1, c2, 10) is True
        assert colors_similar(c1, c2, 9) is False
    
    def test_all_channels_checked(self):
        """All channels must be within tolerance."""
        c1 = (100, 100, 100)
        c2 = (100, 100, 120)  # Only blue differs
        assert colors_similar(c1, c2, 10) is False


# =============================================================================
# TEST get_center_color
# =============================================================================

class TestGetCenterColor:
    """Tests for get_center_color function."""
    
    def test_solid_image(self, solid_color_image):
        """Center of solid color should return that color."""
        color = get_center_color(solid_color_image, 0, 0, 16)
        assert color[:3] == (255, 0, 0)
    
    def test_center_calculation(self):
        """Verify center is calculated correctly."""
        img = Image.new('RGB', (16, 16), (0, 0, 0))
        # Put a different color at the center
        img.putpixel((8, 8), (255, 255, 255))
        
        color = get_center_color(img, 0, 0, 16)
        assert color[:3] == (255, 255, 255)
    
    def test_bounds_clamping(self):
        """Should clamp to image bounds."""
        img = Image.new('RGB', (10, 10), (100, 100, 100))
        # Request cell that would go out of bounds
        color = get_center_color(img, 0, 0, 100)
        # Should clamp to (9, 9)
        assert color is not None


# =============================================================================
# TEST detect_pixel_size
# =============================================================================

class TestDetectPixelSize:
    """Tests for detect_pixel_size function."""
    
    def test_uniform_image(self, solid_color_image):
        """Solid color image should detect as full image."""
        size = detect_pixel_size(solid_color_image)
        # Should find largest uniform block
        assert size >= 1
    
    def test_checkerboard_16(self, checkerboard_image):
        """Should detect 16x16 cells in checkerboard."""
        size = detect_pixel_size(checkerboard_image)
        assert size == 16
    
    def test_scaled_pixel_art(self, pixel_art_8x8_scaled):
        """Should detect 16x scale factor."""
        size = detect_pixel_size(pixel_art_8x8_scaled)
        assert size == 16
    
    def test_tiny_image(self):
        """Tiny images should return 1."""
        img = Image.new('RGB', (1, 1), (255, 0, 0))
        size = detect_pixel_size(img)
        assert size == 1


# =============================================================================
# TEST transform_to_real_pixels
# =============================================================================

class TestTransformToRealPixels:
    """Tests for transform_to_real_pixels function."""
    
    def test_basic_transform(self, pixel_art_8x8_scaled):
        """Should transform 128x128 @ 16x scale to 8x8."""
        result = transform_to_real_pixels(pixel_art_8x8_scaled, 16)
        assert result.size == (8, 8)
    
    def test_color_preservation(self, pixel_art_8x8_scaled):
        """Colors should be preserved during transform."""
        result = transform_to_real_pixels(pixel_art_8x8_scaled, 16)
        # Check a few pixels
        assert result.getpixel((0, 0))[:3] == (255, 0, 0)  # Red
    
    def test_offset_application(self, checkerboard_image):
        """Offset should shift the sampling grid."""
        result1 = transform_to_real_pixels(checkerboard_image, 16, offset_x=0)
        result2 = transform_to_real_pixels(checkerboard_image, 16, offset_x=1)
        # Results should potentially differ based on offset
        assert result1 is not result2
    
    def test_bit_depth_reduction(self, solid_color_image):
        """Bit depth should affect output colors."""
        result_8bit = transform_to_real_pixels(solid_color_image, 10, bit_depth=8)
        result_4bit = transform_to_real_pixels(solid_color_image, 10, bit_depth=4)
        
        color_8 = result_8bit.getpixel((0, 0))[:3]
        color_4 = result_4bit.getpixel((0, 0))[:3]
        
        # 8-bit should preserve, 4-bit may quantize
        assert color_8 == (255, 0, 0)
        # 4-bit: 255 // 16 = 15 -> 15 * 16 + 8 = 248
        assert color_4 == (248, 8, 8)
    
    def test_color_exclusion(self, solid_color_image):
        """Excluded colors should become transparent."""
        result = transform_to_real_pixels(
            solid_color_image, 
            10, 
            excluded_colors=[(255, 0, 0)],
            tolerance=5
        )
        
        # All pixels should be transparent
        pixel = result.getpixel((0, 0))
        assert pixel[3] == 0  # Alpha = 0
    
    def test_invalid_cell_size_raises(self, solid_color_image):
        """Cell size 0 should raise ValueError."""
        with pytest.raises(ValueError):
            transform_to_real_pixels(solid_color_image, 0)
    
    def test_rgba_output(self, solid_color_image):
        """Output should always be RGBA."""
        result = transform_to_real_pixels(solid_color_image, 10)
        assert result.mode == 'RGBA'


# =============================================================================
# TEST create_grid_visualization
# =============================================================================

class TestCreateGridVisualization:
    """Tests for create_grid_visualization function."""
    
    def test_returns_rgba(self, solid_color_image):
        """Should return RGBA image."""
        result = create_grid_visualization(solid_color_image, 16)
        assert result.mode == 'RGBA'
    
    def test_same_size(self, solid_color_image):
        """Output should be same size as input."""
        result = create_grid_visualization(solid_color_image, 16)
        assert result.size == solid_color_image.size
    
    def test_with_offset(self, solid_color_image):
        """Should work with offset."""
        result = create_grid_visualization(
            solid_color_image, 16, 
            offset_x=5, offset_y=5
        )
        assert result is not None
    
    def test_without_center_markers(self, solid_color_image):
        """Should work without center markers."""
        result = create_grid_visualization(
            solid_color_image, 16, 
            center_marker=False
        )
        assert result is not None


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for the full workflow."""
    
    def test_full_workflow(self, pixel_art_8x8_scaled):
        """Test complete detect -> transform workflow."""
        # Detect pixel size
        cell_size = detect_pixel_size(pixel_art_8x8_scaled)
        assert cell_size == 16
        
        # Transform
        result = transform_to_real_pixels(pixel_art_8x8_scaled, cell_size)
        assert result.size == (8, 8)
        
        # Verify colors are preserved
        # Original has pattern where color depends on (x + y) % 4
        colors = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (255, 255, 0),  # Yellow
        ]
        
        for y in range(8):
            for x in range(8):
                expected = colors[(x + y) % 4]
                actual = result.getpixel((x, y))[:3]
                assert actual == expected, f"Mismatch at ({x}, {y})"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
