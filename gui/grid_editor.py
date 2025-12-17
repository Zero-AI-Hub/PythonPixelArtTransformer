"""
Pixel Art Transformer - Advanced Grid Editor Canvas
====================================================
Canvas with manual grid adjustment, non-uniform grids, and cell selection.
"""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Literal, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum

from PIL import Image, ImageTk, ImageDraw

if TYPE_CHECKING:
    from PIL.Image import Image as PILImage

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import ZOOM, UI_COLORS, WINDOW, GRID_EDITOR
from gui.canvases import BaseZoomableCanvas


# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================

class EditorMode(Enum):
    """Editor interaction modes."""
    PAN_ZOOM = "pan_zoom"
    ADJUST_GRID = "adjust_grid"
    SELECT_CELLS = "select_cells"
    AREA_SELECT = "area_select"
    CONTOUR_SELECT = "contour_select"
    DEFINE_PIXEL = "define_pixel"


class DragTarget(Enum):
    """What is being dragged."""
    NONE = "none"
    V_LINE = "v_line"      # Vertical grid line
    H_LINE = "h_line"      # Horizontal grid line
    CORNER = "corner"      # Grid corner (intersection)


@dataclass
class GridConfig:
    """
    Configuration for a non-uniform grid.
    
    The grid is defined by lists of line positions, allowing
    each cell to have a different size.
    """
    # X positions of vertical lines (including left and right edges)
    x_lines: list[int] = field(default_factory=list)
    
    # Y positions of horizontal lines (including top and bottom edges)
    y_lines: list[int] = field(default_factory=list)
    
    # Cells manually excluded (col, row)
    excluded_cells: set[tuple[int, int]] = field(default_factory=set)
    
    # Cells manually included (overrides color exclusion)
    included_cells: set[tuple[int, int]] = field(default_factory=set)
    
    @property
    def num_cols(self) -> int:
        """Number of columns."""
        return max(0, len(self.x_lines) - 1)
    
    @property
    def num_rows(self) -> int:
        """Number of rows."""
        return max(0, len(self.y_lines) - 1)
    
    def get_cell_bounds(self, col: int, row: int) -> tuple[int, int, int, int]:
        """Get (x1, y1, x2, y2) for a cell."""
        if col < 0 or col >= self.num_cols or row < 0 or row >= self.num_rows:
            return (0, 0, 0, 0)
        return (
            self.x_lines[col],
            self.y_lines[row],
            self.x_lines[col + 1],
            self.y_lines[row + 1]
        )
    
    def get_cell_center(self, col: int, row: int) -> tuple[int, int]:
        """Get the center point of a cell."""
        x1, y1, x2, y2 = self.get_cell_bounds(col, row)
        return ((x1 + x2) // 2, (y1 + y2) // 2)
    
    def is_cell_excluded(self, col: int, row: int) -> bool:
        """Check if a cell is excluded."""
        return (col, row) in self.excluded_cells
    
    def is_cell_included(self, col: int, row: int) -> bool:
        """Check if a cell is manually included."""
        return (col, row) in self.included_cells
    
    def toggle_cell(self, col: int, row: int) -> None:
        """Toggle a cell's exclusion state."""
        cell = (col, row)
        if cell in self.excluded_cells:
            self.excluded_cells.remove(cell)
            self.included_cells.add(cell)
        elif cell in self.included_cells:
            self.included_cells.remove(cell)
        else:
            self.excluded_cells.add(cell)
    
    def copy(self) -> 'GridConfig':
        """Create a copy of this config."""
        return GridConfig(
            x_lines=self.x_lines.copy(),
            y_lines=self.y_lines.copy(),
            excluded_cells=self.excluded_cells.copy(),
            included_cells=self.included_cells.copy()
        )
    
    @staticmethod
    def from_uniform(
        width: int, 
        height: int, 
        cell_size: int,
        offset_x: int = 0,
        offset_y: int = 0
    ) -> 'GridConfig':
        """Create a uniform grid from dimensions and cell size."""
        start_x = offset_x if offset_x >= 0 else offset_x % cell_size
        start_y = offset_y if offset_y >= 0 else offset_y % cell_size
        
        x_lines = list(range(start_x, width + 1, cell_size))
        if x_lines and x_lines[-1] < width:
            x_lines.append(width)
        if not x_lines or x_lines[0] > 0:
            x_lines.insert(0, 0)
            
        y_lines = list(range(start_y, height + 1, cell_size))
        if y_lines and y_lines[-1] < height:
            y_lines.append(height)
        if not y_lines or y_lines[0] > 0:
            y_lines.insert(0, 0)
        
        return GridConfig(x_lines=x_lines, y_lines=y_lines)


# =============================================================================
# ADVANCED GRID EDITOR CANVAS
# =============================================================================

class AdvancedGridEditorCanvas(BaseZoomableCanvas):
    """
    Canvas for advanced grid editing with:
    - Manual grid line adjustment by dragging
    - Non-uniform cell sizes
    - Manual cell selection/exclusion
    
    Modes:
    - PAN_ZOOM: Normal zoom/pan behavior
    - ADJUST_GRID: Drag grid lines to resize cells
    - SELECT_CELLS: Click cells to toggle exclusion
    """
    
    def __init__(
        self, 
        parent: tk.Widget,
        on_grid_changed: Callable[[GridConfig], None] | None = None,
        **kwargs
    ):
        """
        Initialize the advanced grid editor.
        
        Args:
            parent: Parent widget.
            on_grid_changed: Callback when grid configuration changes.
            **kwargs: Additional Canvas options.
        """
        super().__init__(
            parent, 
            max_zoom=ZOOM.max_level_editor,
            initial_max_zoom=ZOOM.max_level_initial_editor,
            **kwargs
        )
        
        self.on_grid_changed = on_grid_changed
        
        # Color exclusion settings (for visualization)
        self.excluded_colors: list[tuple[int, int, int] | None] = [None, None]
        self.color_tolerance: int = 10
        
        # Grid configuration
        self.grid_config: GridConfig = GridConfig()
        
        # Editor mode
        self.mode: EditorMode = EditorMode.PAN_ZOOM
        
        # Drag state
        self._drag_target: DragTarget = DragTarget.NONE
        self._drag_line_index: int = -1
        self._drag_start_pos: tuple[int, int] = (0, 0)
        self._drag_original_value: int = 0
        
        # Hover state
        self._hover_line: tuple[DragTarget, int] | None = None
        self._hover_cell: tuple[int, int] | None = None
        
        # Pan state for pan_zoom mode
        self._panning = False
        self._pan_start: tuple[int, int] = (0, 0)
        
        # Eyedropper state
        self._eyedropper_mode = False
        self._eyedropper_callback: Callable[[tuple[int, int, int]], None] | None = None
        
        # Area selection state
        self._area_selecting = False
        self._area_start: tuple[int, int] | None = None  # Image coordinates
        self._area_end: tuple[int, int] | None = None    # Image coordinates
        self._area_rect_id: int | None = None
        
        # Contour selection state
        self._contour_points: list[tuple[int, int]] = []  # Image coordinates
        self._contour_closed = False
        
        # Pixel definition state
        self._pixel_defining = False
        self._pixel_start: tuple[int, int] | None = None  # Image coordinates
        self._pixel_end: tuple[int, int] | None = None    # Image coordinates
        self._on_pixel_defined: Callable[[int, int, int, int], None] | None = None  # (size_w, size_h, off_x, off_y)
        
        # Rebind events
        self.bind('<Motion>', self._on_motion)
        self.bind('<ButtonPress-1>', self._on_press)
        self.bind('<B1-Motion>', self._on_drag)
        self.bind('<ButtonRelease-1>', self._on_release)
        self.bind('<Leave>', self._on_leave)
        self.bind('<ButtonPress-3>', self._on_right_click)
    
    def enable_eyedropper(self, callback: Callable[[tuple[int, int, int]], None]) -> None:
        """
        Enable eyedropper mode for color picking.
        
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
        self._update_cursor()
    
    def set_mode(self, mode: EditorMode) -> None:
        """
        Set the editor mode.
        
        Args:
            mode: New editor mode.
        """
        self.mode = mode
        self._hover_line = None
        self._hover_cell = None
        self._update_cursor()
        self.redraw()
    
    def set_grid_config(self, config: GridConfig) -> None:
        """
        Set the grid configuration.
        
        Args:
            config: New grid configuration.
        """
        self.grid_config = config
        self.redraw()
    
    def reset_to_uniform(self, cell_size: int, offset_x: int = 0, offset_y: int = 0) -> None:
        """
        Reset to a uniform grid.
        
        Args:
            cell_size: Size of each cell.
            offset_x: Horizontal offset.
            offset_y: Vertical offset.
        """
        if self.image is None:
            return
        
        self.grid_config = GridConfig.from_uniform(
            self.image.size[0],
            self.image.size[1],
            cell_size,
            offset_x,
            offset_y
        )
        self._notify_change()
        self.redraw()
    
    def select_all_cells(self) -> None:
        """Mark all cells as included."""
        self.grid_config.excluded_cells.clear()
        self._notify_change()
        self.redraw()
    
    def deselect_all_cells(self) -> None:
        """Mark all cells as excluded."""
        self.grid_config.included_cells.clear()
        for col in range(self.grid_config.num_cols):
            for row in range(self.grid_config.num_rows):
                self.grid_config.excluded_cells.add((col, row))
        self._notify_change()
        self.redraw()
    
    def invert_selection(self) -> None:
        """Invert the exclusion state of all cells."""
        all_cells = set()
        for col in range(self.grid_config.num_cols):
            for row in range(self.grid_config.num_rows):
                all_cells.add((col, row))
        
        # Swap excluded and non-excluded
        new_excluded = all_cells - self.grid_config.excluded_cells
        self.grid_config.excluded_cells = new_excluded
        self.grid_config.included_cells.clear()
        self._notify_change()
        self.redraw()
    
    def _notify_change(self) -> None:
        """Notify that grid config changed."""
        if self.on_grid_changed:
            self.on_grid_changed(self.grid_config)
    
    def get_cells_in_area(self) -> list[tuple[int, int]]:
        """
        Get all cells that are within the current area selection.
        
        Returns:
            List of (col, row) tuples for cells in the selection.
        """
        if self._area_start is None or self._area_end is None:
            return []
        
        # Get the selection bounds in image coordinates
        x1 = min(self._area_start[0], self._area_end[0])
        y1 = min(self._area_start[1], self._area_end[1])
        x2 = max(self._area_start[0], self._area_end[0])
        y2 = max(self._area_start[1], self._area_end[1])
        
        cells = []
        for col in range(self.grid_config.num_cols):
            for row in range(self.grid_config.num_rows):
                cx, cy = self.grid_config.get_cell_center(col, row)
                if x1 <= cx <= x2 and y1 <= cy <= y2:
                    cells.append((col, row))
        
        return cells
    
    def include_cells_in_selection(self) -> int:
        """
        Include (un-exclude) all cells in the current area selection.
        
        Returns:
            Number of cells that were changed.
        """
        cells = self.get_cells_in_area()
        changed = 0
        for col, row in cells:
            if (col, row) in self.grid_config.excluded_cells:
                self.grid_config.excluded_cells.remove((col, row))
                changed += 1
        
        if changed:
            self._notify_change()
            self.redraw()
        return changed
    
    def exclude_cells_in_selection(self) -> int:
        """
        Exclude all cells in the current area selection.
        
        Returns:
            Number of cells that were changed.
        """
        cells = self.get_cells_in_area()
        changed = 0
        for col, row in cells:
            if (col, row) not in self.grid_config.excluded_cells:
                self.grid_config.excluded_cells.add((col, row))
                self.grid_config.included_cells.discard((col, row))
                changed += 1
        
        if changed:
            self._notify_change()
            self.redraw()
        return changed
    
    def clear_area_selection(self) -> None:
        """Clear the current area selection."""
        self._area_start = None
        self._area_end = None
        self._area_selecting = False
        self.redraw()
    
    def has_area_selection(self) -> bool:
        """Check if there is an active area selection."""
        return self._area_start is not None and self._area_end is not None
    
    # =========================================================================
    # CONTOUR SELECTION METHODS
    # =========================================================================
    
    def _point_in_polygon(self, x: int, y: int, polygon: list[tuple[int, int]]) -> bool:
        """
        Check if a point is inside a polygon using ray casting algorithm.
        
        Args:
            x, y: Point coordinates
            polygon: List of (x, y) vertex coordinates
            
        Returns:
            True if point is inside the polygon.
        """
        n = len(polygon)
        if n < 3:
            return False
        
        inside = False
        j = n - 1
        
        for i in range(n):
            xi, yi = polygon[i]
            xj, yj = polygon[j]
            
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            j = i
        
        return inside
    
    def get_cells_in_contour(self) -> list[tuple[int, int]]:
        """
        Get all cells whose centers are inside the current contour polygon.
        
        Returns:
            List of (col, row) tuples for cells inside the contour.
        """
        if not self._contour_closed or len(self._contour_points) < 3:
            return []
        
        cells = []
        for col in range(self.grid_config.num_cols):
            for row in range(self.grid_config.num_rows):
                cx, cy = self.grid_config.get_cell_center(col, row)
                if self._point_in_polygon(cx, cy, self._contour_points):
                    cells.append((col, row))
        
        return cells
    
    def include_cells_in_contour(self) -> int:
        """
        Include (un-exclude) all cells inside the contour polygon.
        
        Returns:
            Number of cells that were changed.
        """
        cells = self.get_cells_in_contour()
        changed = 0
        for col, row in cells:
            if (col, row) in self.grid_config.excluded_cells:
                self.grid_config.excluded_cells.remove((col, row))
                changed += 1
        
        if changed:
            self._notify_change()
            self.redraw()
        return changed
    
    def exclude_cells_outside_contour(self) -> int:
        """
        Exclude all cells outside the contour polygon.
        
        Returns:
            Number of cells that were changed.
        """
        cells_inside = set(self.get_cells_in_contour())
        changed = 0
        
        for col in range(self.grid_config.num_cols):
            for row in range(self.grid_config.num_rows):
                if (col, row) not in cells_inside:
                    if (col, row) not in self.grid_config.excluded_cells:
                        self.grid_config.excluded_cells.add((col, row))
                        self.grid_config.included_cells.discard((col, row))
                        changed += 1
        
        if changed:
            self._notify_change()
            self.redraw()
        return changed
    
    def clear_contour(self) -> None:
        """Clear the current contour polygon."""
        self._contour_points = []
        self._contour_closed = False
        self.redraw()
    
    def close_contour(self) -> None:
        """Close the contour polygon."""
        if len(self._contour_points) >= 3:
            self._contour_closed = True
            self.redraw()
    
    def has_contour(self) -> bool:
        """Check if there is a contour polygon defined."""
        return len(self._contour_points) >= 3
    
    def is_contour_closed(self) -> bool:
        """Check if the contour is closed."""
        return self._contour_closed
    
    def undo_last_contour_point(self) -> None:
        """Remove the last point from the contour."""
        if self._contour_points:
            self._contour_points.pop()
            self._contour_closed = False
            self.redraw()
    
    # =========================================================================
    # PIXEL DEFINITION METHODS
    # =========================================================================
    
    def set_pixel_defined_callback(self, callback: Callable[[int, int, int, int], None] | None) -> None:
        """Set callback for when a pixel is defined. Args: (size_w, size_h, offset_x, offset_y)"""
        self._on_pixel_defined = callback
    
    def get_defined_pixel(self) -> tuple[int, int, int, int] | None:
        """
        Get the defined pixel dimensions and offset.
        
        Returns:
            Tuple of (width, height, offset_x, offset_y) or None if not defined.
        """
        if self._pixel_start is None or self._pixel_end is None:
            return None
        
        x1 = min(self._pixel_start[0], self._pixel_end[0])
        y1 = min(self._pixel_start[1], self._pixel_end[1])
        x2 = max(self._pixel_start[0], self._pixel_end[0])
        y2 = max(self._pixel_start[1], self._pixel_end[1])
        
        width = max(1, x2 - x1)
        height = max(1, y2 - y1)
        
        return (width, height, x1, y1)
    
    def clear_pixel_definition(self) -> None:
        """Clear the pixel definition."""
        self._pixel_start = None
        self._pixel_end = None
        self._pixel_defining = False
        self.redraw()
    
    def has_pixel_definition(self) -> bool:
        """Check if a pixel has been defined."""
        return self._pixel_start is not None and self._pixel_end is not None
    
    def _update_cursor(self) -> None:
        """Update cursor based on mode and hover state."""
        if self.mode == EditorMode.PAN_ZOOM:
            self.config(cursor='')
        elif self.mode == EditorMode.SELECT_CELLS:
            self.config(cursor='hand2')
        elif self.mode == EditorMode.AREA_SELECT:
            self.config(cursor='cross')
        elif self.mode == EditorMode.CONTOUR_SELECT:
            self.config(cursor='pencil')
        elif self.mode == EditorMode.DEFINE_PIXEL:
            self.config(cursor='tcross')
        elif self.mode == EditorMode.ADJUST_GRID:
            if self._hover_line:
                target, _ = self._hover_line
                if target == DragTarget.V_LINE:
                    self.config(cursor='sb_h_double_arrow')
                elif target == DragTarget.H_LINE:
                    self.config(cursor='sb_v_double_arrow')
                elif target == DragTarget.CORNER:
                    self.config(cursor='fleur')
            else:
                self.config(cursor='crosshair')
    
    def redraw(self) -> None:
        """Redraw canvas with grid overlay."""
        if self.image is None:
            return
        
        self.delete("all")
        
        # Draw base image
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
        
        # Draw grid
        self._draw_grid()
        
        # Draw cell overlays
        self._draw_cell_overlays()
        
        # Draw area selection rectangle
        self._draw_area_selection()
        
        # Draw contour polygon
        self._draw_contour()
        
        # Draw pixel definition
        self._draw_pixel_definition()
        
        # Draw info
        self._draw_info_text()
    
    def _draw_grid(self) -> None:
        """Draw grid lines."""
        if not self.grid_config.x_lines or not self.grid_config.y_lines:
            return
        
        # Get image bounds on screen
        img_w, img_h = self.image.size
        
        # Draw vertical lines
        for i, x in enumerate(self.grid_config.x_lines):
            sx = self.img_x + int(x * self.zoom_level)
            sy1 = self.img_y
            sy2 = self.img_y + int(img_h * self.zoom_level)
            
            # Check if hovering
            is_hover = (self._hover_line and 
                       self._hover_line[0] in (DragTarget.V_LINE, DragTarget.CORNER) and 
                       self._hover_line[1] == i)
            
            color = GRID_EDITOR.line_color_hover if is_hover else GRID_EDITOR.line_color_normal
            width = GRID_EDITOR.line_width_hover if is_hover else GRID_EDITOR.line_width_normal
            
            self.create_line(sx, sy1, sx, sy2, fill=color, width=width, tags='grid_line')
        
        # Draw horizontal lines
        for i, y in enumerate(self.grid_config.y_lines):
            sy = self.img_y + int(y * self.zoom_level)
            sx1 = self.img_x
            sx2 = self.img_x + int(img_w * self.zoom_level)
            
            is_hover = (self._hover_line and 
                       self._hover_line[0] in (DragTarget.H_LINE, DragTarget.CORNER) and 
                       self._hover_line[1] == i)
            
            color = GRID_EDITOR.line_color_hover if is_hover else GRID_EDITOR.line_color_normal
            width = GRID_EDITOR.line_width_hover if is_hover else GRID_EDITOR.line_width_normal
            
            self.create_line(sx1, sy, sx2, sy, fill=color, width=width, tags='grid_line')
        
        # Draw center markers
        for col in range(self.grid_config.num_cols):
            for row in range(self.grid_config.num_rows):
                cx, cy = self.grid_config.get_cell_center(col, row)
                scx = self.img_x + int(cx * self.zoom_level)
                scy = self.img_y + int(cy * self.zoom_level)
                
                # Small cross at center (discrete, doesn't obscure image)
                r = max(2, int(2 * self.zoom_level))
                
                # Check if manually excluded
                is_manually_excluded = self.grid_config.is_cell_excluded(col, row)
                
                # Check if color-excluded
                is_color_excluded = False
                if self.image and not is_manually_excluded:
                    # Sample the center color
                    sample_x = max(0, min(cx, self.image.size[0] - 1))
                    sample_y = max(0, min(cy, self.image.size[1] - 1))
                    pixel_color = self.image.getpixel((sample_x, sample_y))[:3]
                    
                    # Check against excluded colors
                    for exc_color in self.excluded_colors:
                        if exc_color is not None:
                            # Simple tolerance check
                            diff = sum(abs(a - b) for a, b in zip(pixel_color, exc_color))
                            if diff <= self.color_tolerance * 3:
                                is_color_excluded = True
                                break
                
                if is_manually_excluded:
                    # X mark for manually excluded (red)
                    self.create_line(
                        scx - r, scy - r, scx + r, scy + r,
                        fill='#ff4444', width=1
                    )
                    self.create_line(
                        scx + r, scy - r, scx - r, scy + r,
                        fill='#ff4444', width=1
                    )
                elif is_color_excluded:
                    # X mark for color-excluded (orange)
                    self.create_line(
                        scx - r, scy - r, scx + r, scy + r,
                        fill='#ff9944', width=1
                    )
                    self.create_line(
                        scx + r, scy - r, scx - r, scy + r,
                        fill='#ff9944', width=1
                    )
                else:
                    # Small + cross for included (discrete green)
                    color = '#88ff88' if self.grid_config.is_cell_included(col, row) else '#44cc44'
                    self.create_line(
                        scx - r, scy, scx + r, scy,
                        fill=color, width=1
                    )
                    self.create_line(
                        scx, scy - r, scx, scy + r,
                        fill=color, width=1
                    )
    
    def _draw_cell_overlays(self) -> None:
        """Draw semi-transparent overlays on cells."""
        if self.mode not in (EditorMode.SELECT_CELLS, EditorMode.AREA_SELECT):
            return
        
        # Get cells in area selection for highlighting
        cells_in_area = set(self.get_cells_in_area()) if self.mode == EditorMode.AREA_SELECT else set()
        
        for col in range(self.grid_config.num_cols):
            for row in range(self.grid_config.num_rows):
                x1, y1, x2, y2 = self.grid_config.get_cell_bounds(col, row)
                
                sx1 = self.img_x + int(x1 * self.zoom_level)
                sy1 = self.img_y + int(y1 * self.zoom_level)
                sx2 = self.img_x + int(x2 * self.zoom_level)
                sy2 = self.img_y + int(y2 * self.zoom_level)
                
                # Hover highlight (SELECT_CELLS mode)
                if self._hover_cell == (col, row) and self.mode == EditorMode.SELECT_CELLS:
                    self.create_rectangle(
                        sx1, sy1, sx2, sy2,
                        fill='#ffff00', 
                        stipple='gray50',
                        outline='#ffff00',
                        width=2,
                        tags='cell_hover'
                    )
                
                # Area selection highlight (AREA_SELECT mode)
                if (col, row) in cells_in_area:
                    self.create_rectangle(
                        sx1, sy1, sx2, sy2,
                        fill='#00aaff', 
                        stipple='gray50',
                        outline='#00aaff',
                        width=1,
                        tags='cell_area'
                    )
                
                # Exclusion overlay
                if self.grid_config.is_cell_excluded(col, row):
                    self.create_rectangle(
                        sx1, sy1, sx2, sy2,
                        fill='#ff0000',
                        stipple='gray25',
                        outline='',
                        tags='cell_excluded'
                    )
    
    def _draw_area_selection(self) -> None:
        """Draw the area selection rectangle."""
        if self.mode != EditorMode.AREA_SELECT:
            return
        
        if self._area_start is None or self._area_end is None:
            return
        
        # Convert image coordinates to screen coordinates
        sx1 = self.img_x + int(self._area_start[0] * self.zoom_level)
        sy1 = self.img_y + int(self._area_start[1] * self.zoom_level)
        sx2 = self.img_x + int(self._area_end[0] * self.zoom_level)
        sy2 = self.img_y + int(self._area_end[1] * self.zoom_level)
        
        # Draw selection rectangle
        self.create_rectangle(
            sx1, sy1, sx2, sy2,
            outline='#00ff88',
            width=2,
            dash=(4, 4),
            tags='area_selection'
        )
    
    def _draw_contour(self) -> None:
        """Draw the contour polygon."""
        if self.mode != EditorMode.CONTOUR_SELECT:
            return
        
        if not self._contour_points:
            return
        
        # Convert image coordinates to screen coordinates
        screen_points = []
        for ix, iy in self._contour_points:
            sx = self.img_x + int(ix * self.zoom_level)
            sy = self.img_y + int(iy * self.zoom_level)
            screen_points.append((sx, sy))
        
        # Draw lines between points
        for i in range(len(screen_points)):
            sx1, sy1 = screen_points[i]
            if i < len(screen_points) - 1:
                sx2, sy2 = screen_points[i + 1]
            elif self._contour_closed:
                sx2, sy2 = screen_points[0]
            else:
                continue
            
            self.create_line(
                sx1, sy1, sx2, sy2,
                fill='#ff00ff',
                width=2,
                tags='contour_line'
            )
        
        # Draw vertices
        for i, (sx, sy) in enumerate(screen_points):
            r = 5
            color = '#00ff00' if i == 0 else '#ff00ff'
            outline = '#ffffff' if i == 0 else '#000000'
            self.create_oval(
                sx - r, sy - r, sx + r, sy + r,
                fill=color,
                outline=outline,
                width=2,
                tags='contour_vertex'
            )
        
        # Highlight cells inside closed contour
        if self._contour_closed:
            cells_inside = self.get_cells_in_contour()
            for col, row in cells_inside:
                x1, y1, x2, y2 = self.grid_config.get_cell_bounds(col, row)
                sx1 = self.img_x + int(x1 * self.zoom_level)
                sy1 = self.img_y + int(y1 * self.zoom_level)
                sx2 = self.img_x + int(x2 * self.zoom_level)
                sy2 = self.img_y + int(y2 * self.zoom_level)
                
                self.create_rectangle(
                    sx1, sy1, sx2, sy2,
                    fill='#ff00ff',
                    stipple='gray50',
                    outline='#ff00ff',
                    width=1,
                    tags='cell_contour'
                )
    
    def _draw_pixel_definition(self) -> None:
        """Draw the pixel definition rectangle."""
        if self.mode != EditorMode.DEFINE_PIXEL:
            return
        
        if self._pixel_start is None:
            return
        
        # Get the current end point (either set or still dragging)
        end = self._pixel_end if self._pixel_end else self._pixel_start
        
        # Convert image coordinates to screen coordinates
        sx1 = self.img_x + int(self._pixel_start[0] * self.zoom_level)
        sy1 = self.img_y + int(self._pixel_start[1] * self.zoom_level)
        sx2 = self.img_x + int(end[0] * self.zoom_level)
        sy2 = self.img_y + int(end[1] * self.zoom_level)
        
        # Draw solid bright rectangle for the defined pixel
        self.create_rectangle(
            sx1, sy1, sx2, sy2,
            outline='#00ff00',
            fill='#00ff00',
            stipple='gray50',
            width=3,
            tags='pixel_definition'
        )
        
        # Draw dimensions text
        if self._pixel_end:
            defined = self.get_defined_pixel()
            if defined:
                w, h, _, _ = defined
                text = f"{w}×{h}"
                self.create_text(
                    (sx1 + sx2) // 2, sy1 - 10,
                    text=text,
                    fill='#00ff00',
                    font=('Segoe UI', 10, 'bold'),
                    tags='pixel_size'
                )
    
    def _draw_info_text(self) -> None:
        """Draw info text."""
        zoom_pct = int(self.zoom_level * 100)
        mode_text = {
            EditorMode.PAN_ZOOM: "🔍 Pan/Zoom",
            EditorMode.ADJUST_GRID: "📏 Ajustar Grid",
            EditorMode.SELECT_CELLS: "✋ Seleccionar",
            EditorMode.AREA_SELECT: "🔲 Área",
            EditorMode.CONTOUR_SELECT: "✏️ Contorno",
            EditorMode.DEFINE_PIXEL: "📍 Definir Píxel"
        }.get(self.mode, "")
        
        cols = self.grid_config.num_cols
        rows = self.grid_config.num_rows
        excluded = len(self.grid_config.excluded_cells)
        
        # Add area selection info
        area_info = ""
        if self.mode == EditorMode.AREA_SELECT and self.has_area_selection():
            cells_in_area = len(self.get_cells_in_area())
            area_info = f" | Selección: {cells_in_area}"
        
        # Add contour info
        if self.mode == EditorMode.CONTOUR_SELECT:
            pts = len(self._contour_points)
            if self._contour_closed:
                cells_inside = len(self.get_cells_in_contour())
                area_info = f" | Cerrado: {cells_inside} celdas"
            elif pts > 0:
                area_info = f" | Puntos: {pts}"
        
        # Add pixel definition info
        if self.mode == EditorMode.DEFINE_PIXEL:
            if self.has_pixel_definition():
                defined = self.get_defined_pixel()
                if defined:
                    w, h, ox, oy = defined
                    area_info = f" | Píxel: {w}×{h} @ ({ox},{oy})"
            else:
                area_info = " | Arrastra sobre un píxel"
        
        info_lines = [
            f"Zoom: {zoom_pct}% | {mode_text}",
            f"Grid: {cols}×{rows} | Excluidas: {excluded}{area_info}"
        ]
        
        for i, line in enumerate(info_lines):
            self.create_text(
                10, 10 + i * 18,
                text=line,
                fill=UI_COLORS.accent_green,
                anchor=tk.NW,
                font=('Segoe UI', 9)
            )
    
    def _find_nearest_line(self, sx: int, sy: int) -> tuple[DragTarget, int] | None:
        """
        Find the nearest grid line to screen coordinates.
        
        Returns:
            Tuple of (target_type, line_index) or None if not near any line.
        """
        if self.image is None:
            return None
        
        grab_dist = GRID_EDITOR.line_grab_distance
        
        # Check vertical lines
        for i, x in enumerate(self.grid_config.x_lines):
            line_sx = self.img_x + int(x * self.zoom_level)
            if abs(sx - line_sx) <= grab_dist:
                # Also check if near a horizontal line (corner)
                for j, y in enumerate(self.grid_config.y_lines):
                    line_sy = self.img_y + int(y * self.zoom_level)
                    if abs(sy - line_sy) <= grab_dist:
                        return (DragTarget.CORNER, i * 1000 + j)  # Encode both indices
                return (DragTarget.V_LINE, i)
        
        # Check horizontal lines
        for i, y in enumerate(self.grid_config.y_lines):
            line_sy = self.img_y + int(y * self.zoom_level)
            if abs(sy - line_sy) <= grab_dist:
                return (DragTarget.H_LINE, i)
        
        return None
    
    def _find_cell_at(self, sx: int, sy: int) -> tuple[int, int] | None:
        """
        Find which cell contains the screen coordinates.
        
        Returns:
            Tuple of (col, row) or None if outside grid.
        """
        if self.image is None:
            return None
        
        # Convert to image coords
        ix = int((sx - self.img_x) / self.zoom_level)
        iy = int((sy - self.img_y) / self.zoom_level)
        
        # Find column
        col = -1
        for i in range(len(self.grid_config.x_lines) - 1):
            if self.grid_config.x_lines[i] <= ix < self.grid_config.x_lines[i + 1]:
                col = i
                break
        
        # Find row
        row = -1
        for i in range(len(self.grid_config.y_lines) - 1):
            if self.grid_config.y_lines[i] <= iy < self.grid_config.y_lines[i + 1]:
                row = i
                break
        
        if col >= 0 and row >= 0:
            return (col, row)
        return None
    
    def _on_motion(self, event: tk.Event) -> None:
        """Handle mouse motion."""
        if self.mode == EditorMode.ADJUST_GRID:
            # Update hover state
            old_hover = self._hover_line
            self._hover_line = self._find_nearest_line(event.x, event.y)
            
            if old_hover != self._hover_line:
                self._update_cursor()
                self.redraw()
        
        elif self.mode == EditorMode.SELECT_CELLS:
            # Update hover cell
            old_hover = self._hover_cell
            self._hover_cell = self._find_cell_at(event.x, event.y)
            
            if old_hover != self._hover_cell:
                self.redraw()
    
    def _on_press(self, event: tk.Event) -> None:
        """Handle mouse press."""
        # Check eyedropper mode first
        if self._eyedropper_mode and self.image:
            ix, iy = self.screen_to_image(event.x, event.y)
            if 0 <= ix < self.image.size[0] and 0 <= iy < self.image.size[1]:
                color = self.image.getpixel((ix, iy))[:3]
                if self._eyedropper_callback:
                    self._eyedropper_callback(color)
            self.disable_eyedropper()
            return
        
        if self.mode == EditorMode.PAN_ZOOM:
            self._panning = True
            self._pan_start = (event.x, event.y)
            self.config(cursor='fleur')
        
        elif self.mode == EditorMode.ADJUST_GRID:
            line = self._find_nearest_line(event.x, event.y)
            if line:
                self._drag_target, self._drag_line_index = line[0], line[1]
                self._drag_start_pos = (event.x, event.y)
                
                # Store original value(s)
                if self._drag_target == DragTarget.V_LINE:
                    idx = self._drag_line_index
                    if 0 < idx < len(self.grid_config.x_lines) - 1:
                        self._drag_original_value = self.grid_config.x_lines[idx]
                elif self._drag_target == DragTarget.H_LINE:
                    idx = self._drag_line_index
                    if 0 < idx < len(self.grid_config.y_lines) - 1:
                        self._drag_original_value = self.grid_config.y_lines[idx]
        
        elif self.mode == EditorMode.SELECT_CELLS:
            cell = self._find_cell_at(event.x, event.y)
            if cell:
                self.grid_config.toggle_cell(cell[0], cell[1])
                self._notify_change()
                self.redraw()
        
        elif self.mode == EditorMode.AREA_SELECT:
            # Start area selection
            ix, iy = self.screen_to_image(event.x, event.y)
            self._area_selecting = True
            self._area_start = (ix, iy)
            self._area_end = (ix, iy)
            self.redraw()
        
        elif self.mode == EditorMode.CONTOUR_SELECT:
            ix, iy = self.screen_to_image(event.x, event.y)
            
            # Check if clicking near first point to close polygon
            if len(self._contour_points) >= 3 and not self._contour_closed:
                first_x, first_y = self._contour_points[0]
                dist = ((ix - first_x) ** 2 + (iy - first_y) ** 2) ** 0.5
                close_threshold = max(10, 20 / self.zoom_level)  # Pixels in image coords
                
                if dist <= close_threshold:
                    self.close_contour()
                    return
            
            # If contour is closed, start a new one
            if self._contour_closed:
                self._contour_points = []
                self._contour_closed = False
            
            # Add new point
            self._contour_points.append((ix, iy))
            self.redraw()
        
        elif self.mode == EditorMode.DEFINE_PIXEL:
            # Start pixel definition
            ix, iy = self.screen_to_image(event.x, event.y)
            self._pixel_defining = True
            self._pixel_start = (ix, iy)
            self._pixel_end = (ix, iy)
            self.redraw()
    
    def _on_drag(self, event: tk.Event) -> None:
        """Handle mouse drag."""
        if self.mode == EditorMode.PAN_ZOOM and self._panning:
            dx = event.x - self._pan_start[0]
            dy = event.y - self._pan_start[1]
            self.offset_x += dx
            self.offset_y += dy
            self._pan_start = (event.x, event.y)
            self.redraw()
        
        elif self.mode == EditorMode.ADJUST_GRID and self._drag_target != DragTarget.NONE:
            self._handle_grid_drag(event)
        
        elif self.mode == EditorMode.SELECT_CELLS:
            # Drag selection - toggle cells as we pass over them
            cell = self._find_cell_at(event.x, event.y)
            if cell and cell != self._hover_cell:
                self._hover_cell = cell
                # Only add to excluded, don't toggle during drag
                if not self.grid_config.is_cell_excluded(cell[0], cell[1]):
                    self.grid_config.excluded_cells.add(cell)
                    self._notify_change()
                    self.redraw()
        
        elif self.mode == EditorMode.AREA_SELECT and self._area_selecting:
            # Update area selection end point
            ix, iy = self.screen_to_image(event.x, event.y)
            self._area_end = (ix, iy)
            self.redraw()
        
        elif self.mode == EditorMode.DEFINE_PIXEL and self._pixel_defining:
            # Update pixel definition end point
            ix, iy = self.screen_to_image(event.x, event.y)
            self._pixel_end = (ix, iy)
            self.redraw()
    
    def _handle_grid_drag(self, event: tk.Event) -> None:
        """Handle dragging grid lines."""
        if self._drag_target == DragTarget.V_LINE:
            idx = self._drag_line_index
            if 0 < idx < len(self.grid_config.x_lines) - 1:
                # Calculate new X position in image coords
                dx_screen = event.x - self._drag_start_pos[0]
                dx_image = int(dx_screen / self.zoom_level)
                new_x = self._drag_original_value + dx_image
                
                # Clamp to valid range
                min_x = self.grid_config.x_lines[idx - 1] + GRID_EDITOR.min_cell_size
                max_x = self.grid_config.x_lines[idx + 1] - GRID_EDITOR.min_cell_size
                new_x = max(min_x, min(max_x, new_x))
                
                self.grid_config.x_lines[idx] = new_x
                self.redraw()
        
        elif self._drag_target == DragTarget.H_LINE:
            idx = self._drag_line_index
            if 0 < idx < len(self.grid_config.y_lines) - 1:
                dy_screen = event.y - self._drag_start_pos[1]
                dy_image = int(dy_screen / self.zoom_level)
                new_y = self._drag_original_value + dy_image
                
                min_y = self.grid_config.y_lines[idx - 1] + GRID_EDITOR.min_cell_size
                max_y = self.grid_config.y_lines[idx + 1] - GRID_EDITOR.min_cell_size
                new_y = max(min_y, min(max_y, new_y))
                
                self.grid_config.y_lines[idx] = new_y
                self.redraw()
        
        elif self._drag_target == DragTarget.CORNER:
            # Decode indices
            v_idx = self._drag_line_index // 1000
            h_idx = self._drag_line_index % 1000
            
            # Move both lines
            if 0 < v_idx < len(self.grid_config.x_lines) - 1:
                dx_screen = event.x - self._drag_start_pos[0]
                dx_image = int(dx_screen / self.zoom_level)
                # This is simplified - would need to store both original values
            
            if 0 < h_idx < len(self.grid_config.y_lines) - 1:
                dy_screen = event.y - self._drag_start_pos[1]
                dy_image = int(dy_screen / self.zoom_level)
            
            self.redraw()
    
    def _on_release(self, event: tk.Event) -> None:
        """Handle mouse release."""
        if self._panning:
            self._panning = False
            self.config(cursor='')
        
        if self._drag_target != DragTarget.NONE:
            self._drag_target = DragTarget.NONE
            self._notify_change()
        
        if self._area_selecting:
            # Finalize area selection (keep it visible)
            ix, iy = self.screen_to_image(event.x, event.y)
            self._area_end = (ix, iy)
            self._area_selecting = False
            self.redraw()
        
        if self._pixel_defining:
            # Finalize pixel definition
            ix, iy = self.screen_to_image(event.x, event.y)
            self._pixel_end = (ix, iy)
            self._pixel_defining = False
            
            # Trigger callback if set
            if self._on_pixel_defined:
                defined = self.get_defined_pixel()
                if defined:
                    w, h, ox, oy = defined
                    self._on_pixel_defined(w, h, ox, oy)
            
            self.redraw()
        
        self._update_cursor()
    
    def _on_leave(self, event: tk.Event) -> None:
        """Handle mouse leaving canvas."""
        if self._hover_line or self._hover_cell:
            self._hover_line = None
            self._hover_cell = None
            self.redraw()
    
    def _on_right_click(self, event: tk.Event) -> None:
        """Handle right mouse click."""
        if self.mode == EditorMode.CONTOUR_SELECT:
            self.undo_last_contour_point()
