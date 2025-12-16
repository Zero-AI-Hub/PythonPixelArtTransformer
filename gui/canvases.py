"""
Pixel Art Transformer - Canvas Components
==========================================
Zoomable canvas widgets for image display and region selection.
"""

from __future__ import annotations

import tkinter as tk
from typing import Callable, TYPE_CHECKING

from PIL import Image, ImageTk

if TYPE_CHECKING:
    from PIL.Image import Image as PILImage

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import ZOOM, UI_COLORS, WINDOW


# =============================================================================
# BASE CANVAS
# =============================================================================

class BaseZoomableCanvas(tk.Canvas):
    """
    Base canvas with zoom and pan functionality.
    
    Provides common functionality for:
    - Mouse wheel zoom centered on cursor
    - Pan with right-click drag
    - Coordinate conversion between screen and image space
    
    Attributes:
        image: The PIL Image being displayed.
        photo: The PhotoImage for Tkinter display.
        zoom_level: Current zoom multiplier.
        offset_x: Horizontal pan offset.
        offset_y: Vertical pan offset.
        img_x: X position of image on canvas.
        img_y: Y position of image on canvas.
    """
    
    def __init__(
        self, 
        parent: tk.Widget, 
        max_zoom: float = ZOOM.max_level_region,
        initial_max_zoom: float = ZOOM.max_level_initial,
        **kwargs
    ):
        """
        Initialize the canvas.
        
        Args:
            parent: Parent widget.
            max_zoom: Maximum zoom level allowed.
            initial_max_zoom: Maximum zoom for initial view fitting.
            **kwargs: Additional Canvas options.
        """
        super().__init__(parent, **kwargs)
        
        self.image: PILImage | None = None
        self.photo: ImageTk.PhotoImage | None = None
        
        self.zoom_level: float = ZOOM.default
        self.max_zoom: float = max_zoom
        self.initial_max_zoom: float = initial_max_zoom
        
        self.offset_x: int = 0
        self.offset_y: int = 0
        self.img_x: int = 0
        self.img_y: int = 0
        
        # Pan state
        self._pan_start: tuple[int, int] | None = None
        
        # Bind events
        self.bind('<MouseWheel>', self._on_mousewheel)
        self.bind('<Button-4>', self._on_mousewheel)  # Linux scroll up
        self.bind('<Button-5>', self._on_mousewheel)  # Linux scroll down
        self.bind('<ButtonPress-3>', self._on_pan_start)
        self.bind('<B3-Motion>', self._on_pan)
        self.bind('<Configure>', lambda e: self.redraw())
    
    def set_image(self, image: PILImage) -> None:
        """
        Set the image to display.
        
        Args:
            image: PIL Image to display.
        """
        self.image = image
        self.reset_view()
        self.redraw()
    
    def reset_view(self) -> None:
        """Reset zoom and pan to fit image in canvas."""
        if self.image is None:
            return
        
        self.update_idletasks()
        canvas_w = self.winfo_width()
        canvas_h = self.winfo_height()
        
        if canvas_w > WINDOW.min_canvas_size and canvas_h > WINDOW.min_canvas_size:
            img_w, img_h = self.image.size
            self.zoom_level = min(
                canvas_w / img_w, 
                canvas_h / img_h, 
                self.initial_max_zoom
            )
        
        self.offset_x = 0
        self.offset_y = 0
    
    def redraw(self) -> None:
        """Redraw the canvas with current image and zoom."""
        if self.image is None:
            return
        
        self.delete("all")
        
        img_w, img_h = self.image.size
        new_w = max(1, int(img_w * self.zoom_level))
        new_h = max(1, int(img_h * self.zoom_level))
        
        resized = self.image.resize((new_w, new_h), Image.Resampling.NEAREST)
        self.photo = ImageTk.PhotoImage(resized)
        
        canvas_w = self.winfo_width()
        canvas_h = self.winfo_height()
        self.img_x = (canvas_w - new_w) // 2 + self.offset_x
        self.img_y = (canvas_h - new_h) // 2 + self.offset_y
        
        self.create_image(self.img_x, self.img_y, anchor=tk.NW, image=self.photo)
        
        # Draw zoom info
        zoom_pct = int(self.zoom_level * 100)
        self._draw_info(zoom_pct)
    
    def _draw_info(self, zoom_pct: int) -> None:
        """Draw info text. Override in subclasses."""
        self.create_text(
            10, 10, 
            text=f"Zoom: {zoom_pct}%", 
            fill=UI_COLORS.accent_green, 
            anchor=tk.NW, 
            font=('Segoe UI', 9)
        )
    
    def screen_to_image(self, sx: int, sy: int) -> tuple[int, int]:
        """
        Convert screen coordinates to image coordinates.
        
        Args:
            sx: Screen X coordinate.
            sy: Screen Y coordinate.
        
        Returns:
            Tuple of (image_x, image_y), clamped to image bounds.
        """
        ix = int((sx - self.img_x) / self.zoom_level)
        iy = int((sy - self.img_y) / self.zoom_level)
        
        if self.image:
            ix = max(0, min(ix, self.image.size[0] - 1))
            iy = max(0, min(iy, self.image.size[1] - 1))
        
        return ix, iy
    
    def image_to_screen(self, ix: int, iy: int) -> tuple[int, int]:
        """
        Convert image coordinates to screen coordinates.
        
        Args:
            ix: Image X coordinate.
            iy: Image Y coordinate.
        
        Returns:
            Tuple of (screen_x, screen_y).
        """
        sx = self.img_x + int(ix * self.zoom_level)
        sy = self.img_y + int(iy * self.zoom_level)
        return sx, sy
    
    def _on_mousewheel(self, event: tk.Event) -> None:
        """Handle mouse wheel zoom."""
        if self.image is None:
            return
        
        # Determine zoom direction
        # On Linux, Button-4 is scroll up, Button-5 is scroll down
        # On Windows/macOS, use event.delta (positive = up, negative = down)
        if event.num == 4:  # Linux scroll up
            factor = ZOOM.zoom_factor_in
        elif event.num == 5:  # Linux scroll down
            factor = ZOOM.zoom_factor_out
        elif hasattr(event, 'delta') and event.delta != 0:
            factor = ZOOM.zoom_factor_in if event.delta > 0 else ZOOM.zoom_factor_out
        else:
            return  # Unknown event
        
        new_zoom = max(ZOOM.min_level, min(self.max_zoom, self.zoom_level * factor))
        
        if new_zoom != self.zoom_level:
            # Zoom centered on mouse position
            canvas_w = self.winfo_width()
            canvas_h = self.winfo_height()
            mouse_x = event.x - canvas_w // 2
            mouse_y = event.y - canvas_h // 2
            
            ratio = new_zoom / self.zoom_level
            self.offset_x = int(mouse_x - (mouse_x - self.offset_x) * ratio)
            self.offset_y = int(mouse_y - (mouse_y - self.offset_y) * ratio)
            self.zoom_level = new_zoom
            
            self.redraw()
    
    def _on_pan_start(self, event: tk.Event) -> None:
        """Start panning."""
        self._pan_start = (event.x, event.y)
    
    def _on_pan(self, event: tk.Event) -> None:
        """Handle pan motion."""
        if self._pan_start is None:
            return
        
        dx = event.x - self._pan_start[0]
        dy = event.y - self._pan_start[1]
        self.offset_x += dx
        self.offset_y += dy
        self._pan_start = (event.x, event.y)
        
        self.redraw()


# =============================================================================
# REGION SELECT CANVAS
# =============================================================================

class RegionSelectCanvas(BaseZoomableCanvas):
    """
    Canvas for selecting rectangular regions on an image.
    
    Allows drawing rectangles to define regions for processing.
    Left-click and drag to create regions.
    """
    
    def __init__(
        self, 
        parent: tk.Widget, 
        on_region_added: Callable[[int, tuple[int, int, int, int]], None] | None = None,
        **kwargs
    ):
        """
        Initialize the region select canvas.
        
        Args:
            parent: Parent widget.
            on_region_added: Callback when a region is added. 
                           Receives (index, (x1, y1, x2, y2)).
            **kwargs: Additional Canvas options.
        """
        super().__init__(parent, max_zoom=ZOOM.max_level_region, **kwargs)
        
        self.on_region_added = on_region_added
        self.regions: list[tuple[int, int, int, int]] = []
        
        # Selection state
        self._selecting = False
        self._select_start: tuple[int, int] | None = None
        self._current_rect: int | None = None
        
        # Bind selection events
        self.bind('<ButtonPress-1>', self._on_press)
        self.bind('<B1-Motion>', self._on_motion)
        self.bind('<ButtonRelease-1>', self._on_release)
    
    def set_image(self, image: PILImage) -> None:
        """Set image and clear regions."""
        self.regions = []
        super().set_image(image)
    
    def redraw(self) -> None:
        """Redraw with regions overlay."""
        super().redraw()
        
        if self.image is None:
            return
        
        # Draw existing regions
        for i, (x1, y1, x2, y2) in enumerate(self.regions):
            sx1, sy1 = self.image_to_screen(x1, y1)
            sx2, sy2 = self.image_to_screen(x2, y2)
            
            self.create_rectangle(
                sx1, sy1, sx2, sy2, 
                outline=UI_COLORS.region_outline, 
                width=2, 
                tags=f'region_{i}'
            )
            self.create_text(
                sx1 + 5, sy1 + 5, 
                text=str(i + 1), 
                fill=UI_COLORS.region_outline,
                anchor=tk.NW, 
                font=('Segoe UI', 10, 'bold')
            )
    
    def _draw_info(self, zoom_pct: int) -> None:
        """Draw info with region count."""
        self.create_text(
            10, 10, 
            text=f"Zoom: {zoom_pct}% | Regiones: {len(self.regions)}", 
            fill=UI_COLORS.accent_green, 
            anchor=tk.NW, 
            font=('Segoe UI', 9)
        )
        self.create_text(
            10, 28, 
            text="Click+arrastrar: seleccionar | Click derecho: mover", 
            fill=UI_COLORS.muted, 
            anchor=tk.NW, 
            font=('Segoe UI', 8)
        )
    
    def _on_press(self, event: tk.Event) -> None:
        """Start region selection."""
        self._selecting = True
        self._select_start = (event.x, event.y)
    
    def _on_motion(self, event: tk.Event) -> None:
        """Update selection rectangle."""
        if not self._selecting or self._select_start is None:
            return
        
        if self._current_rect:
            self.delete(self._current_rect)
        
        self._current_rect = self.create_rectangle(
            self._select_start[0], self._select_start[1], 
            event.x, event.y,
            outline=UI_COLORS.selection_rect, 
            width=2, 
            dash=(4, 4)
        )
    
    def _on_release(self, event: tk.Event) -> None:
        """Complete region selection."""
        if not self._selecting or self._select_start is None:
            return
        
        self._selecting = False
        
        if self._current_rect:
            self.delete(self._current_rect)
            self._current_rect = None
        
        # Convert to image coordinates
        x1, y1 = self.screen_to_image(*self._select_start)
        x2, y2 = self.screen_to_image(event.x, event.y)
        
        # Normalize
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        
        # Validate minimum size
        from config import REGION
        if (x2 - x1) >= REGION.min_region_size and (y2 - y1) >= REGION.min_region_size:
            self.regions.append((x1, y1, x2, y2))
            if self.on_region_added:
                self.on_region_added(len(self.regions) - 1, (x1, y1, x2, y2))
            self.redraw()
        
        self._select_start = None
    
    def remove_region(self, index: int) -> None:
        """Remove a region by index."""
        if 0 <= index < len(self.regions):
            del self.regions[index]
            self.redraw()
    
    def clear_regions(self) -> None:
        """Remove all regions."""
        self.regions = []
        self.redraw()
    
    def get_regions(self) -> list[tuple[int, int, int, int]]:
        """Get copy of all regions."""
        return self.regions.copy()


# =============================================================================
# REGION EDITOR CANVAS
# =============================================================================

class RegionEditorCanvas(BaseZoomableCanvas):
    """
    Canvas for editing a single region with eyedropper tool.
    
    Supports:
    - Left-click drag to pan (when not in eyedropper mode)
    - Eyedropper mode for color picking
    """
    
    def __init__(self, parent: tk.Widget, **kwargs):
        """
        Initialize the editor canvas.
        
        Args:
            parent: Parent widget.
            **kwargs: Additional Canvas options.
        """
        super().__init__(
            parent, 
            max_zoom=ZOOM.max_level_editor, 
            initial_max_zoom=ZOOM.max_level_initial_editor,
            **kwargs
        )
        
        # Eyedropper state
        self._eyedropper_mode = False
        self._eyedropper_callback: Callable[[tuple[int, int, int]], None] | None = None
        
        # Drag state
        self._dragging = False
        self._drag_start: tuple[int, int] = (0, 0)
        
        # Override left-click for pan/eyedropper
        self.bind('<ButtonPress-1>', self._on_click)
        self.bind('<B1-Motion>', self._on_drag)
        self.bind('<ButtonRelease-1>', self._on_drag_end)
    
    def enable_eyedropper(self, callback: Callable[[tuple[int, int, int]], None]) -> None:
        """
        Enable eyedropper mode.
        
        Args:
            callback: Function to call with picked color (R, G, B).
        """
        self._eyedropper_mode = True
        self._eyedropper_callback = callback
        self.config(cursor='crosshair')
    
    def disable_eyedropper(self) -> None:
        """Disable eyedropper mode."""
        self._eyedropper_mode = False
        self._eyedropper_callback = None
        self.config(cursor='')
    
    def _draw_info(self, zoom_pct: int) -> None:
        """Draw info with eyedropper status."""
        mode_text = " [🎯 EYEDROPPER]" if self._eyedropper_mode else ""
        self.create_text(
            10, 10, 
            text=f"Zoom: {zoom_pct}%{mode_text}", 
            fill=UI_COLORS.accent_green, 
            anchor=tk.NW, 
            font=('Segoe UI', 9)
        )
    
    def _on_click(self, event: tk.Event) -> None:
        """Handle left click - eyedropper or start pan."""
        if self._eyedropper_mode and self.image:
            ix, iy = self.screen_to_image(event.x, event.y)
            if 0 <= ix < self.image.size[0] and 0 <= iy < self.image.size[1]:
                color = self.image.getpixel((ix, iy))[:3]
                if self._eyedropper_callback:
                    self._eyedropper_callback(color)
            self.disable_eyedropper()
            return
        
        self._dragging = True
        self._drag_start = (event.x, event.y)
        self.config(cursor='fleur')
    
    def _on_drag(self, event: tk.Event) -> None:
        """Handle drag for panning."""
        if not self._dragging:
            return
        
        dx = event.x - self._drag_start[0]
        dy = event.y - self._drag_start[1]
        self.offset_x += dx
        self.offset_y += dy
        self._drag_start = (event.x, event.y)
        
        self.redraw()
    
    def _on_drag_end(self, event: tk.Event) -> None:
        """End drag."""
        self._dragging = False
        self.config(cursor='')
