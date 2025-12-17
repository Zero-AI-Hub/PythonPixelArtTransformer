"""
Pixel Art Transformer - Step Frame Components
==============================================
Individual step frames for the wizard-style interface.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Callable, TYPE_CHECKING

from PIL import Image

if TYPE_CHECKING:
    from PIL.Image import Image as PILImage

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import UI_COLORS, REGION, COLOR, FILE
from core import draw_grid_overlay, detect_pixel_size, transform_to_real_pixels
from core.exceptions import InvalidImageError
from gui.canvases import RegionSelectCanvas, RegionEditorCanvas


# =============================================================================
# TYPE ALIASES
# =============================================================================

RegionConfig = dict
Color = tuple[int, int, int]


# =============================================================================
# STEP 1: LOAD IMAGE
# =============================================================================

class Step1Frame(ttk.Frame):
    """
    Step 1: Load image frame.
    
    Provides a simple interface to load an image file.
    Supports drag and drop on Windows.
    """
    
    def __init__(
        self, 
        parent: tk.Widget, 
        on_image_loaded: Callable[[PILImage, Path], None]
    ):
        """
        Initialize Step 1 frame.
        
        Args:
            parent: Parent widget.
            on_image_loaded: Callback when image is loaded (image, path).
        """
        super().__init__(parent)
        
        self.on_image_loaded = on_image_loaded
        self._create_widgets()
        self._setup_drag_drop()
    
    def _create_widgets(self) -> None:
        """Create the UI widgets."""
        from PIL import Image, ImageTk
        
        # Try to load and display the icon as background
        icon_path = Path(__file__).parent.parent / "assets" / "icon.png"
        self.bg_icon = None
        
        if icon_path.exists():
            try:
                img = Image.open(icon_path)
                # Resize for background display
                img = img.resize((200, 200), Image.Resampling.NEAREST)
                self.bg_icon = ImageTk.PhotoImage(img)
            except Exception:
                pass
        
        # Background icon label (behind everything)
        if self.bg_icon:
            bg_label = tk.Label(self, image=self.bg_icon, bg=UI_COLORS.background)
            bg_label.place(relx=0.5, rely=0.4, anchor=tk.CENTER)
        
        center = ttk.Frame(self)
        center.place(relx=0.5, rely=0.65, anchor=tk.CENTER)
        
        ttk.Label(
            center, 
            text="Arrastra una imagen o haz click para cargar", 
            style='Info.TLabel'
        ).pack(pady=10)
        
        load_btn = ttk.Button(
            center, 
            text="📂 Cargar Imagen", 
            command=self._load_image,
            style='Accent.TButton'
        )
        load_btn.pack(pady=10)
        
        self.load_info = ttk.Label(center, text="", style='Info.TLabel')
        self.load_info.pack()
        
        # Drop zone indicator
        self.drop_label = ttk.Label(
            center,
            text="",
            style='Info.TLabel'
        )
        self.drop_label.pack(pady=10)
    
    def _setup_drag_drop(self) -> None:
        """Setup drag and drop if available."""
        try:
            # Try to use tkinterdnd2 if available
            self.drop_target_register = None  # Placeholder
            self.drop_label.config(text="💡 Arrastra archivos aquí")
        except Exception:
            pass
    
    def _load_image(self) -> None:
        """Open file dialog and load image."""
        filetypes = list(FILE.supported_formats)
        filepath = filedialog.askopenfilename(
            title="Seleccionar imagen", 
            filetypes=filetypes
        )
        
        if filepath:
            self._process_file(filepath)
    
    def _process_file(self, filepath: str) -> None:
        """Load and validate an image file."""
        try:
            path = Path(filepath)
            image = Image.open(filepath)
            
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            self.load_info.config(
                text=f"✅ {path.name}\n{image.size[0]}×{image.size[1]}"
            )
            
            self.on_image_loaded(image, path)
            
        except FileNotFoundError:
            raise InvalidImageError(filepath, "File not found")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la imagen:\n{e}")


# =============================================================================
# STEP 2: SELECT REGIONS
# =============================================================================

class Step2Frame(ttk.Frame):
    """
    Step 2: Region selection frame.
    
    Allows drawing rectangles to define regions for processing.
    """
    
    def __init__(
        self,
        parent: tk.Widget,
        on_back: Callable[[], None],
        on_continue: Callable[[list[RegionConfig]], None]
    ):
        """
        Initialize Step 2 frame.
        
        Args:
            parent: Parent widget.
            on_back: Callback for back button.
            on_continue: Callback for continue button (receives region configs).
        """
        super().__init__(parent)
        
        self.on_back = on_back
        self.on_continue = on_continue
        self.regions: list[RegionConfig] = []
        
        self._create_widgets()
    
    def _create_widgets(self) -> None:
        """Create the UI widgets."""
        # Left panel - controls
        left = ttk.Frame(self, width=200)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        left.pack_propagate(False)
        
        ttk.Label(
            left, 
            text="Selecciona las figuras", 
            style='Title.TLabel'
        ).pack(pady=5)
        
        ttk.Label(
            left, 
            text="Dibuja rectángulos sobre\ncada sprite o figura", 
            style='Info.TLabel'
        ).pack(pady=5)
        
        self.regions_list = tk.Listbox(
            left, 
            bg=UI_COLORS.secondary_bg, 
            fg=UI_COLORS.foreground, 
            height=8,
            selectbackground=UI_COLORS.accent
        )
        self.regions_list.pack(fill=tk.X, padx=5, pady=5)
        
        btn_frame = ttk.Frame(left)
        btn_frame.pack(fill=tk.X, padx=5)
        
        ttk.Button(
            btn_frame, 
            text="🗑️ Eliminar", 
            command=self._remove_selected_region
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            btn_frame, 
            text="🧹 Limpiar", 
            command=self._clear_all_regions
        ).pack(side=tk.RIGHT)
        
        ttk.Separator(left, orient='horizontal').pack(fill=tk.X, pady=10)
        
        nav_frame = ttk.Frame(left)
        nav_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            nav_frame, 
            text="← Atrás", 
            command=self.on_back
        ).pack(side=tk.LEFT)
        
        self.next_btn = ttk.Button(
            nav_frame, 
            text="Continuar →", 
            command=self._on_continue,
            style='Accent.TButton'
        )
        self.next_btn.pack(side=tk.RIGHT)
        
        # Canvas
        self.canvas = RegionSelectCanvas(
            self, 
            bg=UI_COLORS.canvas_bg, 
            highlightthickness=0,
            on_region_added=self._on_region_added
        )
        self.canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
    
    def set_image(self, image: PILImage) -> None:
        """Set the image to display."""
        self.canvas.set_image(image)
        self.regions = []
        self._update_regions_list()
    
    def _on_region_added(self, idx: int, coords: tuple[int, int, int, int]) -> None:
        """Handle new region added."""
        self.regions.append({
            'coords': coords,
            'grid_size': REGION.default_grid_size,
            'auto_detect': True,
            'offset_x': 0,
            'offset_y': 0,
            'bits': COLOR.default_bit_depth,
            'excluded_colors': [None, None],
            'tolerance': REGION.default_tolerance,
        })
        self._update_regions_list()
    
    def _update_regions_list(self) -> None:
        """Update the regions listbox."""
        self.regions_list.delete(0, tk.END)
        for i, region in enumerate(self.regions):
            x1, y1, x2, y2 = region['coords']
            self.regions_list.insert(tk.END, f"Región {i+1}: {x2-x1}×{y2-y1}")
    
    def _remove_selected_region(self) -> None:
        """Remove the selected region."""
        sel = self.regions_list.curselection()
        if sel:
            idx = sel[0]
            del self.regions[idx]
            self.canvas.remove_region(idx)
            self._update_regions_list()
    
    def _clear_all_regions(self) -> None:
        """Clear all regions."""
        self.regions = []
        self.canvas.clear_regions()
        self._update_regions_list()
    
    def _on_continue(self) -> None:
        """Handle continue button."""
        if not self.regions:
            messagebox.showwarning("Aviso", "Selecciona al menos una región")
            return
        self.on_continue(self.regions)


# =============================================================================
# STEP 3: EDIT REGIONS (ADVANCED)
# =============================================================================

class Step3Frame(ttk.Frame):
    """
    Step 3: Advanced region editing frame.
    
    Features:
    - Manual grid line adjustment by dragging
    - Non-uniform cell sizes
    - Manual cell selection/exclusion
    - Multiple interaction modes
    """
    
    def __init__(
        self,
        parent: tk.Widget,
        on_back: Callable[[], None],
        on_generate: Callable[[list[RegionConfig]], None]
    ):
        """
        Initialize Step 3 frame.
        
        Args:
            parent: Parent widget.
            on_back: Callback for back button.
            on_generate: Callback for generate button.
        """
        super().__init__(parent)
        
        self.on_back = on_back
        self.on_generate = on_generate
        
        self.original_image: PILImage | None = None
        self.regions: list[RegionConfig] = []
        self.current_region_idx: int = 0
        self.current_region_image: PILImage | None = None
        self.excluded_colors: list[Color | None] = [None, None]
        
        # Import here to avoid circular imports
        from gui.grid_editor import AdvancedGridEditorCanvas, GridConfig, EditorMode
        self.GridConfig = GridConfig
        self.EditorMode = EditorMode
        self.AdvancedGridEditorCanvas = AdvancedGridEditorCanvas
        
        self._create_widgets()
    
    def _create_widgets(self) -> None:
        """Create the UI widgets."""
        # Left panel - controls with scrollbar
        left_container = ttk.Frame(self, width=260)
        left_container.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        left_container.pack_propagate(False)
        
        # Create canvas and scrollbar for scrolling
        self.left_canvas = tk.Canvas(
            left_container, 
            bg=UI_COLORS.background, 
            highlightthickness=0,
            width=245
        )
        scrollbar = ttk.Scrollbar(left_container, orient="vertical", command=self.left_canvas.yview)
        
        # Create frame inside canvas to hold all widgets
        left = ttk.Frame(self.left_canvas)
        
        # Configure scroll region
        def configure_scroll(event):
            self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all"))
        
        left.bind("<Configure>", configure_scroll)
        
        # Create window in canvas
        self.left_canvas.create_window((0, 0), window=left, anchor="nw")
        self.left_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack scrollbar and canvas
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Enable mouse wheel scrolling
        def on_mousewheel(event):
            self.left_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.left_canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        # Region navigation
        nav_region = ttk.Frame(left)
        nav_region.pack(fill=tk.X, padx=5, pady=5)
        
        self.prev_btn = ttk.Button(
            nav_region, text="◀", width=3, 
            command=self._prev_region
        )
        self.prev_btn.pack(side=tk.LEFT)
        
        self.region_indicator = ttk.Label(
            nav_region, 
            text="Región 1/1", 
            style='Title.TLabel'
        )
        self.region_indicator.pack(side=tk.LEFT, expand=True)
        
        self.next_btn = ttk.Button(
            nav_region, text="▶", width=3, 
            command=self._next_region
        )
        self.next_btn.pack(side=tk.RIGHT)
        
        ttk.Separator(left, orient='horizontal').pack(fill=tk.X, pady=5)
        
        # ===== MODE TOOLBAR =====
        mode_frame = ttk.LabelFrame(left, text="🎯 Modo de Edición", padding=5)
        mode_frame.pack(fill=tk.X, padx=5, pady=3)
        
        self.current_mode = tk.StringVar(value="define_pixel")
        
        modes = [
            ("📍 Definir Píxel", "define_pixel"),
            ("🔍 Pan/Zoom", "pan_zoom"),
            ("📏 Ajustar Grid", "adjust_grid"),
            ("✋ Seleccionar", "select_cells"),
            ("🔲 Área", "area_select"),
            ("✏️ Contorno", "contour_select"),
        ]
        
        for text, value in modes:
            ttk.Radiobutton(
                mode_frame, text=text, value=value,
                variable=self.current_mode,
                command=self._on_mode_changed
            ).pack(anchor=tk.W)
        
        # Apply pixel definition button
        self.apply_pixel_btn = ttk.Button(
            mode_frame, text="✓ Aplicar Píxel",
            command=self._apply_pixel_definition
        )
        self.apply_pixel_btn.pack(fill=tk.X, pady=(5, 0))
        
        # Mode help text
        self.mode_help = ttk.Label(
            mode_frame, text="Arrastra sobre UN píxel para definir el grid",
            style='Info.TLabel', wraplength=200
        )
        self.mode_help.pack(anchor=tk.W, pady=(5, 0))
        
        ttk.Separator(left, orient='horizontal').pack(fill=tk.X, pady=5)
        
        # ===== GRID SETTINGS =====
        grid_frame = ttk.LabelFrame(left, text="📐 Grid Inicial", padding=5)
        grid_frame.pack(fill=tk.X, padx=5, pady=3)
        
        self.auto_detect = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            grid_frame, text="Auto-detectar", 
            variable=self.auto_detect,
            command=self._on_auto_detect_changed
        ).pack(anchor=tk.W)
        
        size_frame = ttk.Frame(grid_frame)
        size_frame.pack(fill=tk.X)
        ttk.Label(size_frame, text="Tamaño:").pack(side=tk.LEFT)
        
        self.grid_size = tk.IntVar(value=REGION.default_grid_size)
        self.grid_spin = ttk.Spinbox(
            size_frame, 
            from_=REGION.min_grid_size, 
            to=REGION.max_grid_size, 
            width=4,
            textvariable=self.grid_size
        )
        self.grid_spin.pack(side=tk.RIGHT)
        self.grid_spin.bind('<Return>', lambda e: self._apply_uniform_grid())
        
        # Offset
        off_row = ttk.Frame(grid_frame)
        off_row.pack(fill=tk.X, pady=2)
        
        ttk.Label(off_row, text="Offset X:").pack(side=tk.LEFT)
        self.offset_x = tk.IntVar(value=0)
        ttk.Spinbox(
            off_row, from_=-32, to=32, width=4, 
            textvariable=self.offset_x
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(off_row, text="Y:").pack(side=tk.LEFT)
        self.offset_y = tk.IntVar(value=0)
        ttk.Spinbox(
            off_row, from_=-32, to=32, width=4, 
            textvariable=self.offset_y
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            grid_frame, text="Aplicar Grid Uniforme",
            command=self._apply_uniform_grid
        ).pack(fill=tk.X, pady=(5, 0))
        
        ttk.Separator(left, orient='horizontal').pack(fill=tk.X, pady=5)
        
        # ===== CELL SELECTION TOOLS =====
        sel_frame = ttk.LabelFrame(left, text="✋ Selección de Celdas", padding=5)
        sel_frame.pack(fill=tk.X, padx=5, pady=3)
        
        btn_row1 = ttk.Frame(sel_frame)
        btn_row1.pack(fill=tk.X)
        
        ttk.Button(
            btn_row1, text="✓ Todo",
            command=self._select_all_cells, width=8
        ).pack(side=tk.LEFT, padx=1)
        
        ttk.Button(
            btn_row1, text="✗ Nada",
            command=self._deselect_all_cells, width=8
        ).pack(side=tk.LEFT, padx=1)
        
        ttk.Button(
            btn_row1, text="↔ Invertir",
            command=self._invert_selection, width=8
        ).pack(side=tk.LEFT, padx=1)
        
        # ===== AREA SELECTION BUTTONS =====
        area_label = ttk.Label(sel_frame, text="Selección por área:", style='Info.TLabel')
        area_label.pack(anchor=tk.W, pady=(5, 2))
        
        btn_row2 = ttk.Frame(sel_frame)
        btn_row2.pack(fill=tk.X)
        
        ttk.Button(
            btn_row2, text="✓ Incluir",
            command=self._include_area_selection, width=8
        ).pack(side=tk.LEFT, padx=1)
        
        ttk.Button(
            btn_row2, text="✗ Excluir",
            command=self._exclude_area_selection, width=8
        ).pack(side=tk.LEFT, padx=1)
        
        ttk.Button(
            btn_row2, text="⌫ Limpiar",
            command=self._clear_area_selection, width=8
        ).pack(side=tk.LEFT, padx=1)
        
        # ===== CONTOUR SELECTION BUTTONS =====
        contour_label = ttk.Label(sel_frame, text="Selección por contorno:", style='Info.TLabel')
        contour_label.pack(anchor=tk.W, pady=(5, 2))
        
        btn_row3 = ttk.Frame(sel_frame)
        btn_row3.pack(fill=tk.X)
        
        ttk.Button(
            btn_row3, text="✓ Interior",
            command=self._include_contour_cells, width=8
        ).pack(side=tk.LEFT, padx=1)
        
        ttk.Button(
            btn_row3, text="✗ Exterior",
            command=self._exclude_outside_contour, width=8
        ).pack(side=tk.LEFT, padx=1)
        
        ttk.Button(
            btn_row3, text="⌫ Limpiar",
            command=self._clear_contour, width=8
        ).pack(side=tk.LEFT, padx=1)
        
        self.cell_info = ttk.Label(
            sel_frame, text="Celdas: 0×0 | Excluidas: 0",
            style='Info.TLabel'
        )
        self.cell_info.pack(anchor=tk.W, pady=(5, 0))
        
        ttk.Separator(left, orient='horizontal').pack(fill=tk.X, pady=5)
        
        # ===== COLOR SETTINGS =====
        bits_frame = ttk.LabelFrame(left, text="🎨 Colores", padding=5)
        bits_frame.pack(fill=tk.X, padx=5, pady=3)
        
        self.bits = tk.IntVar(value=COLOR.default_bit_depth)
        bits_row = ttk.Frame(bits_frame)
        bits_row.pack(fill=tk.X)
        for txt, val in COLOR.bit_depth_options:
            ttk.Radiobutton(
                bits_row, text=txt, value=val, 
                variable=self.bits
            ).pack(side=tk.LEFT)
        
        # Exclude colors by eyedropper
        exc_row = ttk.Frame(bits_frame)
        exc_row.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(exc_row, text="Excluir:").pack(side=tk.LEFT)
        
        self.exc_color1 = tk.Frame(
            exc_row, bg='#333', 
            width=25, height=20, 
            relief=tk.RAISED, bd=1
        )
        self.exc_color1.pack(side=tk.LEFT, padx=2)
        self.exc_color1.bind('<Button-1>', lambda e: self._pick_exclude_color(0))
        
        self.exc_color2 = tk.Frame(
            exc_row, bg='#333', 
            width=25, height=20, 
            relief=tk.RAISED, bd=1
        )
        self.exc_color2.pack(side=tk.LEFT, padx=2)
        self.exc_color2.bind('<Button-1>', lambda e: self._pick_exclude_color(1))
        
        ttk.Button(
            exc_row, text="✕", width=2, 
            command=self._clear_exclude_colors
        ).pack(side=tk.LEFT, padx=2)
        
        # Tolerance
        tol_row = ttk.Frame(bits_frame)
        tol_row.pack(fill=tk.X, pady=2)
        ttk.Label(tol_row, text="Tolerancia:").pack(side=tk.LEFT)
        
        self.tolerance = tk.IntVar(value=REGION.default_tolerance)
        ttk.Scale(
            tol_row, 
            from_=0, to=50, 
            variable=self.tolerance, 
            orient=tk.HORIZONTAL
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Separator(left, orient='horizontal').pack(fill=tk.X, pady=5)
        
        # ===== NAVIGATION =====
        main_nav = ttk.Frame(left)
        main_nav.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            main_nav, text="← Regiones", 
            command=self.on_back
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            main_nav, text="Generar →", 
            command=self._on_generate,
            style='Accent.TButton'
        ).pack(side=tk.RIGHT)
        
        # ===== CANVAS =====
        self.canvas = self.AdvancedGridEditorCanvas(
            self, 
            bg=UI_COLORS.canvas_bg, 
            highlightthickness=0,
            on_grid_changed=self._on_grid_changed
        )
        self.canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
    
    def _on_mode_changed(self) -> None:
        """Handle mode selection change."""
        mode_str = self.current_mode.get()
        mode = self.EditorMode(mode_str)
        self.canvas.set_mode(mode)
        
        # Update help text
        help_texts = {
            "define_pixel": "Arrastra sobre UN píxel para definir tamaño y posición del grid",
            "pan_zoom": "Scroll: zoom | Click derecho: pan",
            "adjust_grid": "Arrastrar líneas del grid para ajustar",
            "select_cells": "Click en celdas para excluir/incluir",
            "area_select": "Dibuja un área y usa botones para incluir/excluir",
            "contour_select": "Click para añadir puntos. Click cerca del inicio para cerrar. Click derecho: deshacer",
        }
        self.mode_help.config(text=help_texts.get(mode_str, ""))
    
    def _apply_pixel_definition(self) -> None:
        """Apply the pixel definition to set up the grid."""
        if not self.canvas.has_pixel_definition():
            messagebox.showinfo("Info", "Primero arrastra sobre un píxel para definirlo")
            return
        
        defined = self.canvas.get_defined_pixel()
        if not defined:
            return
        
        width, height, offset_x, offset_y = defined
        
        # Use the larger dimension as cell size (for square cells)
        # or average for rectangular
        cell_size = max(width, height)
        
        # Update UI values
        self.grid_size.set(cell_size)
        self.offset_x.set(offset_x % cell_size)  # Wrap offset to grid period
        self.offset_y.set(offset_y % cell_size)
        
        # Apply the grid
        self.canvas.reset_to_uniform(cell_size, offset_x % cell_size, offset_y % cell_size)
        self._update_cell_info()
        
        # Clear the pixel definition visualization
        self.canvas.clear_pixel_definition()
        
        # Switch to pan/zoom mode
        self.current_mode.set("pan_zoom")
        self._on_mode_changed()
        
        messagebox.showinfo(
            "Grid Aplicado",
            f"✅ Grid configurado:\n"
            f"• Tamaño de celda: {cell_size}px\n"
            f"• Offset: ({offset_x % cell_size}, {offset_y % cell_size})"
        )
    
    def _on_auto_detect_changed(self) -> None:
        """Handle auto-detect checkbox change."""
        if self.auto_detect.get() and self.current_region_image:
            detected = detect_pixel_size(self.current_region_image)
            self.grid_size.set(detected)
            self._apply_uniform_grid()
    
    def _apply_uniform_grid(self) -> None:
        """Apply uniform grid based on current settings."""
        if self.current_region_image is None:
            return
        
        cell_size = self.grid_size.get()
        off_x = self.offset_x.get()
        off_y = self.offset_y.get()
        
        self.canvas.reset_to_uniform(cell_size, off_x, off_y)
        self._update_cell_info()
    
    def _select_all_cells(self) -> None:
        """Mark all cells as included."""
        self.canvas.select_all_cells()
        self._update_cell_info()
    
    def _deselect_all_cells(self) -> None:
        """Mark all cells as excluded."""
        self.canvas.deselect_all_cells()
        self._update_cell_info()
    
    def _invert_selection(self) -> None:
        """Invert cell selection."""
        self.canvas.invert_selection()
        self._update_cell_info()
    
    def _include_area_selection(self) -> None:
        """Include all cells in the area selection."""
        if not self.canvas.has_area_selection():
            messagebox.showinfo("Info", "Dibuja primero un área en modo '🔲 Área'")
            return
        changed = self.canvas.include_cells_in_selection()
        self._update_cell_info()
    
    def _exclude_area_selection(self) -> None:
        """Exclude all cells in the area selection."""
        if not self.canvas.has_area_selection():
            messagebox.showinfo("Info", "Dibuja primero un área en modo '🔲 Área'")
            return
        changed = self.canvas.exclude_cells_in_selection()
        self._update_cell_info()
    
    def _clear_area_selection(self) -> None:
        """Clear the area selection."""
        self.canvas.clear_area_selection()
    
    def _include_contour_cells(self) -> None:
        """Include all cells inside the contour."""
        if not self.canvas.is_contour_closed():
            messagebox.showinfo("Info", "Dibuja y cierra primero un contorno en modo '✏️ Contorno'")
            return
        changed = self.canvas.include_cells_in_contour()
        self._update_cell_info()
    
    def _exclude_outside_contour(self) -> None:
        """Exclude all cells outside the contour."""
        if not self.canvas.is_contour_closed():
            messagebox.showinfo("Info", "Dibuja y cierra primero un contorno en modo '✏️ Contorno'")
            return
        changed = self.canvas.exclude_cells_outside_contour()
        self._update_cell_info()
    
    def _clear_contour(self) -> None:
        """Clear the contour."""
        self.canvas.clear_contour()
    
    def _on_grid_changed(self, config) -> None:
        """Handle grid configuration change from canvas."""
        self._update_cell_info()
    
    def _update_cell_info(self) -> None:
        """Update cell info label."""
        config = self.canvas.grid_config
        cols = config.num_cols
        rows = config.num_rows
        excluded = len(config.excluded_cells)
        self.cell_info.config(text=f"Celdas: {cols}×{rows} | Excluidas: {excluded}")
    
    def _validate_int(self, value: str) -> bool:
        """Validate integer input."""
        if value == "":
            return True
        try:
            int(value)
            return True
        except ValueError:
            return False
    
    def set_data(self, image: PILImage, regions: list[RegionConfig]) -> None:
        """Set the image and regions to edit."""
        self.original_image = image
        self.regions = regions
        self.current_region_idx = 0
        self._load_current_region()
    
    def _load_current_region(self) -> None:
        """Load the current region into the editor."""
        if not self.regions or self.original_image is None:
            return
        
        region = self.regions[self.current_region_idx]
        x1, y1, x2, y2 = region['coords']
        
        # Extract subimage
        self.current_region_image = self.original_image.crop((x1, y1, x2, y2))
        
        # Set image on canvas
        self.canvas.set_image(self.current_region_image)
        
        # Load configuration
        self.auto_detect.set(region.get('auto_detect', True))
        self.grid_size.set(region.get('grid_size', REGION.default_grid_size))
        self.offset_x.set(region.get('offset_x', 0))
        self.offset_y.set(region.get('offset_y', 0))
        self.bits.set(region.get('bits', COLOR.default_bit_depth))
        self.tolerance.set(region.get('tolerance', REGION.default_tolerance))
        self.excluded_colors = region.get('excluded_colors', [None, None]).copy()
        
        # Update color frames
        for i, color in enumerate(self.excluded_colors):
            frame = self.exc_color1 if i == 0 else self.exc_color2
            if color:
                frame.config(bg='#{:02x}{:02x}{:02x}'.format(*color))
            else:
                frame.config(bg='#333')
        
        # Load or create grid config
        if 'grid_config' in region:
            self.canvas.set_grid_config(region['grid_config'])
        else:
            # Calculate a sensible default grid size based on image dimensions
            img_w, img_h = self.current_region_image.size
            min_dim = min(img_w, img_h)
            
            # Target around 20-40 cells per dimension for good performance
            # This calculates a grid size that gives approximately 30 cells
            calculated_size = max(REGION.min_grid_size, min_dim // 30)
            
            # Try auto-detect first
            if self.auto_detect.get():
                detected = detect_pixel_size(self.current_region_image)
                # Only use detected size if it's reasonable (not 1)
                if detected > 1:
                    self.grid_size.set(detected)
                else:
                    # Fall back to calculated size
                    self.grid_size.set(min(calculated_size, REGION.max_grid_size))
            else:
                # Use calculated size as default
                self.grid_size.set(min(calculated_size, REGION.max_grid_size))
            
            self._apply_uniform_grid()
        
        self._update_indicator()
        self._update_cell_info()
    
    def _save_current_region_config(self) -> None:
        """Save current region configuration."""
        if not self.regions:
            return
        
        self.regions[self.current_region_idx].update({
            'auto_detect': self.auto_detect.get(),
            'grid_size': self.grid_size.get(),
            'offset_x': self.offset_x.get(),
            'offset_y': self.offset_y.get(),
            'bits': self.bits.get(),
            'excluded_colors': self.excluded_colors.copy(),
            'tolerance': self.tolerance.get(),
            'grid_config': self.canvas.grid_config.copy(),
        })
    
    def _update_indicator(self) -> None:
        """Update region indicator."""
        self.region_indicator.config(
            text=f"Región {self.current_region_idx + 1}/{len(self.regions)}"
        )
        
        # Update navigation buttons
        self.prev_btn.state(
            ['!disabled'] if self.current_region_idx > 0 else ['disabled']
        )
        self.next_btn.state(
            ['!disabled'] if self.current_region_idx < len(self.regions) - 1 else ['disabled']
        )
    
    def _prev_region(self) -> None:
        """Go to previous region."""
        self._save_current_region_config()
        if self.current_region_idx > 0:
            self.current_region_idx -= 1
            self._load_current_region()
    
    def _next_region(self) -> None:
        """Go to next region."""
        self._save_current_region_config()
        if self.current_region_idx < len(self.regions) - 1:
            self.current_region_idx += 1
            self._load_current_region()
    
    def _pick_exclude_color(self, idx: int) -> None:
        """Activate eyedropper to pick exclude color."""
        # Enable eyedropper mode on canvas
        self.canvas.enable_eyedropper(
            lambda c: self._set_exclude_color(idx, c)
        )
    
    def _set_exclude_color(self, idx: int, color: Color) -> None:
        """Set an excluded color."""
        self.excluded_colors[idx] = color
        frame = self.exc_color1 if idx == 0 else self.exc_color2
        frame.config(bg='#{:02x}{:02x}{:02x}'.format(*color))
        
        # Sync with canvas and redraw
        self.canvas.excluded_colors = self.excluded_colors.copy()
        self.canvas.color_tolerance = self.tolerance.get()
        self.canvas.redraw()
    
    def _clear_exclude_colors(self) -> None:
        """Clear all excluded colors."""
        self.excluded_colors = [None, None]
        self.exc_color1.config(bg='#333')
        self.exc_color2.config(bg='#333')
        
        # Sync with canvas and redraw
        self.canvas.excluded_colors = [None, None]
        self.canvas.redraw()
    
    def _on_generate(self) -> None:
        """Handle generate button."""
        self._save_current_region_config()
        self.on_generate(self.regions)


# =============================================================================
# STEP 4: RESULTS
# =============================================================================

class Step4Frame(ttk.Frame):
    """
    Step 4: Results display frame.
    
    Shows generated images and provides save options.
    """
    
    def __init__(
        self,
        parent: tk.Widget,
        on_back: Callable[[], None],
        on_new: Callable[[], None]
    ):
        """
        Initialize Step 4 frame.
        
        Args:
            parent: Parent widget.
            on_back: Callback for back button.
            on_new: Callback for new image button.
        """
        super().__init__(parent)
        
        self.on_back = on_back
        self.on_new = on_new
        
        self.results: dict[int, PILImage] = {}
        self.original_path: Path | None = None
        
        self._create_widgets()
    
    def _create_widgets(self) -> None:
        """Create the UI widgets."""
        # Left panel
        left = ttk.Frame(self, width=220)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        left.pack_propagate(False)
        
        ttk.Label(
            left, text="✅ Completado", 
            style='Title.TLabel'
        ).pack(pady=10)
        
        self.result_info = ttk.Label(
            left, text="", 
            style='Info.TLabel', 
            wraplength=200
        )
        self.result_info.pack(pady=5)
        
        # ===== OUTPUT SIZE PRESETS =====
        size_frame = ttk.LabelFrame(left, text="📐 Tamaño de Salida", padding=5)
        size_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.output_size = tk.StringVar(value="1:1 Píxel")
        size_combo = ttk.Combobox(
            size_frame,
            textvariable=self.output_size,
            values=[name for name, _ in FILE.output_size_presets],
            state='readonly',
            width=12
        )
        size_combo.pack(side=tk.LEFT, padx=2)
        size_combo.bind('<<ComboboxSelected>>', self._on_size_changed)
        
        self.size_info = ttk.Label(
            size_frame, text="(mínima memoria)",
            style='Info.TLabel'
        )
        self.size_info.pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(left, orient='horizontal').pack(fill=tk.X, pady=5)
        
        ttk.Button(
            left, text="💾 Guardar Todo", 
            command=self._save_all,
            style='Accent.TButton'
        ).pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            left, text="💾 Guardar Seleccionado", 
            command=self._save_selected
        ).pack(fill=tk.X, padx=5)
        
        # ===== CLIPBOARD EXPORT =====
        clip_frame = ttk.LabelFrame(left, text="📋 Copiar al Portapapeles", padding=5)
        clip_frame.pack(fill=tk.X, padx=5, pady=5)
        
        clip_row1 = ttk.Frame(clip_frame)
        clip_row1.pack(fill=tk.X)
        
        ttk.Button(
            clip_row1, text="Bytes",
            command=lambda: self._copy_to_clipboard("bytes"), width=7
        ).pack(side=tk.LEFT, padx=1)
        
        ttk.Button(
            clip_row1, text="Base64",
            command=lambda: self._copy_to_clipboard("base64"), width=7
        ).pack(side=tk.LEFT, padx=1)
        
        clip_row2 = ttk.Frame(clip_frame)
        clip_row2.pack(fill=tk.X, pady=(2, 0))
        
        ttk.Button(
            clip_row2, text="NumPy",
            command=lambda: self._copy_to_clipboard("numpy"), width=7
        ).pack(side=tk.LEFT, padx=1)
        
        ttk.Button(
            clip_row2, text="Bitmap",
            command=lambda: self._copy_to_clipboard("bitmap"), width=7
        ).pack(side=tk.LEFT, padx=1)
        
        ttk.Separator(left, orient='horizontal').pack(fill=tk.X, pady=10)
        
        self.result_list = tk.Listbox(
            left, 
            bg=UI_COLORS.secondary_bg, 
            fg=UI_COLORS.foreground, 
            height=10,
            selectbackground=UI_COLORS.accent
        )
        self.result_list.pack(fill=tk.BOTH, expand=True, padx=5)
        self.result_list.bind('<<ListboxSelect>>', self._on_result_select)
        
        ttk.Separator(left, orient='horizontal').pack(fill=tk.X, pady=10)
        
        ttk.Button(
            left, text="← Editar regiones", 
            command=self.on_back
        ).pack(fill=tk.X, padx=5)
        
        ttk.Button(
            left, text="🔄 Nueva imagen", 
            command=self.on_new
        ).pack(fill=tk.X, padx=5, pady=5)
        
        # Canvas
        self.canvas = RegionEditorCanvas(
            self, 
            bg=UI_COLORS.canvas_bg, 
            highlightthickness=0
        )
        self.canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
    
    def _get_target_size(self) -> int:
        """Get the target output size from the selected preset."""
        selected = self.output_size.get()
        for name, size in FILE.output_size_presets:
            if name == selected:
                return size
        return 0  # Original
    
    def _resize_image(self, img: PILImage, target_size: int) -> PILImage:
        """
        Resize image to target size while maintaining aspect ratio.
        
        For square targets, the image is resized to fit within the target
        and centered on a transparent canvas.
        """
        if target_size == 0:
            return img
        
        orig_w, orig_h = img.size
        
        # Calculate scaling to fit within target
        scale = min(target_size / orig_w, target_size / orig_h)
        new_w = int(orig_w * scale)
        new_h = int(orig_h * scale)
        
        # Resize with nearest neighbor to preserve pixel art crispness
        resized = img.resize((new_w, new_h), Image.Resampling.NEAREST)
        
        # Create canvas and center the image
        canvas = Image.new('RGBA', (target_size, target_size), (0, 0, 0, 0))
        offset_x = (target_size - new_w) // 2
        offset_y = (target_size - new_h) // 2
        canvas.paste(resized, (offset_x, offset_y))
        
        return canvas
    
    def _on_size_changed(self, event: tk.Event = None) -> None:
        """Handle output size preset change."""
        target = self._get_target_size()
        if target == 0:
            self.size_info.config(text="(mínima memoria)")
        else:
            self.size_info.config(text=f"→ {target}×{target}px")
    
    def _get_selected_image(self) -> PILImage | None:
        """Get the currently selected result image."""
        sel = self.result_list.curselection()
        if not sel:
            return None
        idx = list(self.results.keys())[sel[0]]
        return self.results.get(idx)
    
    def _copy_to_clipboard(self, format_type: str) -> None:
        """
        Copy the selected image to clipboard in the specified format.
        
        Args:
            format_type: One of 'bytes', 'base64', 'numpy', 'bitmap'
        """
        import io
        import base64
        
        img = self._get_selected_image()
        if img is None:
            messagebox.showinfo("Info", "Selecciona primero una región de la lista")
            return
        
        # Resize if needed
        target_size = self._get_target_size()
        img = self._resize_image(img, target_size)
        
        try:
            if format_type == "bytes":
                # Raw bytes as Python literal
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                raw_bytes = buffer.getvalue()
                text = repr(raw_bytes)
                
            elif format_type == "base64":
                # Base64 encoded string
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                text = b64
                
            elif format_type == "numpy":
                # NumPy array representation
                try:
                    import numpy as np
                    arr = np.array(img)
                    text = f"np.array({arr.tolist()}, dtype=np.uint8)  # shape: {arr.shape}"
                except ImportError:
                    # If numpy not available, use list format
                    pixels = list(img.getdata())
                    w, h = img.size
                    text = f"# Image {w}x{h}, RGBA\n{pixels}"
                    
            elif format_type == "bitmap":
                # Bitmap as binary string (1-bit representation)
                gray = img.convert('L')
                w, h = gray.size
                lines = []
                lines.append(f"# Bitmap {w}x{h}")
                for y in range(h):
                    row = ""
                    for x in range(w):
                        pixel = gray.getpixel((x, y))
                        row += "█" if pixel > 127 else " "
                    lines.append(f'"{row}"')
                text = "\n".join(lines)
            else:
                text = ""
            
            # Copy to clipboard
            self.clipboard_clear()
            self.clipboard_append(text)
            self.update()  # Required for clipboard to persist
            
            # Show success
            size_kb = len(text) / 1024
            messagebox.showinfo(
                "Copiado", 
                f"✅ Copiado al portapapeles\nFormato: {format_type}\nTamaño: {size_kb:.1f} KB"
            )
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al copiar:\n{e}")
    
    def set_results(
        self, 
        results: dict[int, PILImage], 
        original_path: Path
    ) -> None:
        """Set the results to display."""
        self.results = results
        self.original_path = original_path
        
        self.result_list.delete(0, tk.END)
        for idx, img in results.items():
            self.result_list.insert(
                tk.END, 
                f"Región {idx+1}: {img.size[0]}×{img.size[1]}"
            )
        
        self.result_info.config(text=f"✅ {len(results)} regiones generadas")
        
        if results:
            self.result_list.selection_set(0)
            first_idx = list(results.keys())[0]
            self.canvas.set_image(results[first_idx])
    
    def _on_result_select(self, event: tk.Event) -> None:
        """Handle result selection."""
        sel = self.result_list.curselection()
        if sel:
            idx = list(self.results.keys())[sel[0]]
            if idx in self.results:
                self.canvas.set_image(self.results[idx])
    
    def _save_all(self) -> None:
        """Save all results."""
        if not self.results or not self.original_path:
            return
        
        target_size = self._get_target_size()
        size_suffix = f"_{target_size}x{target_size}" if target_size > 0 else ""
        
        folder = filedialog.askdirectory(title="Seleccionar carpeta")
        if folder:
            try:
                for idx, img in self.results.items():
                    # Resize if needed
                    output_img = self._resize_image(img, target_size)
                    name = f"{self.original_path.stem}{FILE.region_suffix}{idx+1}{size_suffix}.png"
                    output_img.save(Path(folder) / name, FILE.output_format)
                
                size_text = f" ({target_size}×{target_size}px)" if target_size > 0 else ""
                messagebox.showinfo(
                    "Guardado", 
                    f"{len(self.results)} imágenes guardadas{size_text} en:\n{folder}"
                )
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar:\n{e}")
    
    def _save_selected(self) -> None:
        """Save selected result."""
        sel = self.result_list.curselection()
        if not sel or not self.original_path:
            return
        
        idx = list(self.results.keys())[sel[0]]
        if idx not in self.results:
            return
        
        target_size = self._get_target_size()
        size_suffix = f"_{target_size}x{target_size}" if target_size > 0 else ""
        
        default_name = f"{self.original_path.stem}{FILE.region_suffix}{idx+1}{size_suffix}.png"
        filepath = filedialog.asksaveasfilename(
            title="Guardar",
            defaultextension=".png",
            initialfile=default_name,
            filetypes=[("PNG", "*.png")]
        )
        
        if filepath:
            try:
                # Resize if needed
                output_img = self._resize_image(self.results[idx], target_size)
                output_img.save(filepath, FILE.output_format)
                
                size_text = f" ({target_size}×{target_size}px)" if target_size > 0 else ""
                messagebox.showinfo("Guardado", f"Imagen guardada{size_text}:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar:\n{e}")
