"""
Pixel Art Transformer - Interfaz Gráfica v6
============================================
Flujo de trabajo:
1. Cargar imagen
2. Seleccionar regiones (rectángulos) con las figuras
3. Procesar cada región individualmente con su configuración
4. Generar todas las regiones transformadas

Optimizado para 1920x1080
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from PIL import Image, ImageTk, ImageDraw
import numpy as np
from pathlib import Path


class RegionSelectCanvas(tk.Canvas):
    """Canvas para seleccionar regiones rectangulares."""
    
    def __init__(self, parent, on_region_added=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.image = None
        self.photo = None
        self.on_region_added = on_region_added
        
        self.zoom_level = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.img_x = 0
        self.img_y = 0
        
        # Selección de rectángulo
        self.selecting = False
        self.select_start = None
        self.current_rect = None
        self.regions = []  # Lista de (x1, y1, x2, y2) en coords de imagen
        
        # Modo
        self.mode = 'select'  # 'select' o 'pan'
        
        self.bind('<MouseWheel>', self.on_mousewheel)
        self.bind('<Button-4>', self.on_mousewheel)
        self.bind('<Button-5>', self.on_mousewheel)
        self.bind('<ButtonPress-1>', self.on_press)
        self.bind('<B1-Motion>', self.on_motion)
        self.bind('<ButtonRelease-1>', self.on_release)
        self.bind('<ButtonPress-3>', self.on_pan_start)
        self.bind('<B3-Motion>', self.on_pan)
        self.bind('<Configure>', lambda e: self.redraw())
        
    def set_image(self, image):
        self.image = image
        self.regions = []
        self.reset_view()
        self.redraw()
        
    def reset_view(self):
        if self.image is None:
            return
        self.update_idletasks()
        canvas_w = self.winfo_width()
        canvas_h = self.winfo_height()
        if canvas_w > 10 and canvas_h > 10:
            img_w, img_h = self.image.size
            self.zoom_level = min(canvas_w / img_w, canvas_h / img_h, 2.0)
        self.offset_x = 0
        self.offset_y = 0
        
    def redraw(self):
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
        
        # Dibujar regiones existentes
        for i, (x1, y1, x2, y2) in enumerate(self.regions):
            sx1 = self.img_x + int(x1 * self.zoom_level)
            sy1 = self.img_y + int(y1 * self.zoom_level)
            sx2 = self.img_x + int(x2 * self.zoom_level)
            sy2 = self.img_y + int(y2 * self.zoom_level)
            self.create_rectangle(sx1, sy1, sx2, sy2, outline='#00ff88', width=2, tags=f'region_{i}')
            self.create_text(sx1 + 5, sy1 + 5, text=str(i + 1), fill='#00ff88', 
                           anchor=tk.NW, font=('Segoe UI', 10, 'bold'))
        
        # Info
        zoom_pct = int(self.zoom_level * 100)
        self.create_text(10, 10, text=f"Zoom: {zoom_pct}% | Regiones: {len(self.regions)}", 
                        fill='#00ff88', anchor=tk.NW, font=('Segoe UI', 9))
        self.create_text(10, 28, text="Click+arrastrar: seleccionar | Click derecho: mover", 
                        fill='#888888', anchor=tk.NW, font=('Segoe UI', 8))
        
    def screen_to_image(self, sx, sy):
        ix = int((sx - self.img_x) / self.zoom_level)
        iy = int((sy - self.img_y) / self.zoom_level)
        if self.image:
            ix = max(0, min(ix, self.image.size[0]))
            iy = max(0, min(iy, self.image.size[1]))
        return ix, iy
        
    def on_press(self, event):
        self.selecting = True
        self.select_start = (event.x, event.y)
        
    def on_motion(self, event):
        if not self.selecting or not self.select_start:
            return
        if self.current_rect:
            self.delete(self.current_rect)
        self.current_rect = self.create_rectangle(
            self.select_start[0], self.select_start[1], event.x, event.y,
            outline='#e94560', width=2, dash=(4, 4)
        )
        
    def on_release(self, event):
        if not self.selecting or not self.select_start:
            return
        self.selecting = False
        if self.current_rect:
            self.delete(self.current_rect)
            self.current_rect = None
            
        # Convertir a coords de imagen
        x1, y1 = self.screen_to_image(*self.select_start)
        x2, y2 = self.screen_to_image(event.x, event.y)
        
        # Normalizar
        if x1 > x2: x1, x2 = x2, x1
        if y1 > y2: y1, y2 = y2, y1
        
        # Mínimo 10x10 pixeles
        if x2 - x1 >= 10 and y2 - y1 >= 10:
            self.regions.append((x1, y1, x2, y2))
            if self.on_region_added:
                self.on_region_added(len(self.regions) - 1, (x1, y1, x2, y2))
            self.redraw()
            
        self.select_start = None
        
    def on_pan_start(self, event):
        self.pan_start = (event.x, event.y)
        
    def on_pan(self, event):
        if hasattr(self, 'pan_start'):
            dx = event.x - self.pan_start[0]
            dy = event.y - self.pan_start[1]
            self.offset_x += dx
            self.offset_y += dy
            self.pan_start = (event.x, event.y)
            self.redraw()
            
    def on_mousewheel(self, event):
        if self.image is None:
            return
        factor = 1.2 if (event.num == 4 or event.delta > 0) else 0.8
        new_zoom = max(0.1, min(10.0, self.zoom_level * factor))
        if new_zoom != self.zoom_level:
            canvas_w = self.winfo_width()
            canvas_h = self.winfo_height()
            mouse_x = event.x - canvas_w // 2
            mouse_y = event.y - canvas_h // 2
            ratio = new_zoom / self.zoom_level
            self.offset_x = int(mouse_x - (mouse_x - self.offset_x) * ratio)
            self.offset_y = int(mouse_y - (mouse_y - self.offset_y) * ratio)
            self.zoom_level = new_zoom
            self.redraw()
            
    def remove_region(self, index):
        if 0 <= index < len(self.regions):
            del self.regions[index]
            self.redraw()
            
    def clear_regions(self):
        self.regions = []
        self.redraw()
        
    def get_regions(self):
        return self.regions.copy()


class RegionEditorCanvas(tk.Canvas):
    """Canvas para editar una región individual con grid."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.image = None
        self.photo = None
        self.zoom_level = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.img_x = 0
        self.img_y = 0
        
        # Eyedropper
        self.eyedropper_mode = False
        self.eyedropper_callback = None
        
        self.bind('<MouseWheel>', self.on_mousewheel)
        self.bind('<ButtonPress-1>', self.on_click)
        self.bind('<B1-Motion>', self.on_drag)
        self.bind('<ButtonRelease-1>', lambda e: setattr(self, 'dragging', False))
        self.bind('<Configure>', lambda e: self.redraw())
        
        self.dragging = False
        self.drag_start = (0, 0)
        
    def set_image(self, image):
        self.image = image
        self.reset_view()
        self.redraw()
        
    def reset_view(self):
        if self.image is None:
            return
        self.update_idletasks()
        canvas_w = self.winfo_width()
        canvas_h = self.winfo_height()
        if canvas_w > 10 and canvas_h > 10:
            img_w, img_h = self.image.size
            self.zoom_level = min(canvas_w / img_w, canvas_h / img_h, 4.0)
        self.offset_x = 0
        self.offset_y = 0
        
    def redraw(self):
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
        
        zoom_pct = int(self.zoom_level * 100)
        mode_text = " [🎯 EYEDROPPER]" if self.eyedropper_mode else ""
        self.create_text(10, 10, text=f"Zoom: {zoom_pct}%{mode_text}", 
                        fill='#00ff88', anchor=tk.NW, font=('Segoe UI', 9))
        
    def enable_eyedropper(self, callback):
        self.eyedropper_mode = True
        self.eyedropper_callback = callback
        self.config(cursor='crosshair')
        
    def disable_eyedropper(self):
        self.eyedropper_mode = False
        self.eyedropper_callback = None
        self.config(cursor='')
        
    def screen_to_image(self, sx, sy):
        ix = int((sx - self.img_x) / self.zoom_level)
        iy = int((sy - self.img_y) / self.zoom_level)
        return ix, iy
        
    def on_click(self, event):
        if self.eyedropper_mode and self.image:
            ix, iy = self.screen_to_image(event.x, event.y)
            if 0 <= ix < self.image.size[0] and 0 <= iy < self.image.size[1]:
                color = self.image.getpixel((ix, iy))[:3]
                if self.eyedropper_callback:
                    self.eyedropper_callback(color)
            self.disable_eyedropper()
            return
        self.dragging = True
        self.drag_start = (event.x, event.y)
        self.config(cursor='fleur')
        
    def on_drag(self, event):
        if not self.dragging:
            return
        dx = event.x - self.drag_start[0]
        dy = event.y - self.drag_start[1]
        self.offset_x += dx
        self.offset_y += dy
        self.drag_start = (event.x, event.y)
        self.redraw()
        
    def on_mousewheel(self, event):
        if self.image is None:
            return
        factor = 1.2 if (event.num == 4 or event.delta > 0) else 0.8
        new_zoom = max(0.1, min(20.0, self.zoom_level * factor))
        if new_zoom != self.zoom_level:
            canvas_w = self.winfo_width()
            canvas_h = self.winfo_height()
            mouse_x = event.x - canvas_w // 2
            mouse_y = event.y - canvas_h // 2
            ratio = new_zoom / self.zoom_level
            self.offset_x = int(mouse_x - (mouse_x - self.offset_x) * ratio)
            self.offset_y = int(mouse_y - (mouse_y - self.offset_y) * ratio)
            self.zoom_level = new_zoom
            self.redraw()


class PixelArtTransformerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎨 Pixel Art Transformer v6")
        self.root.geometry("1280x720")
        self.root.minsize(1024, 600)
        
        self.original_image = None
        self.original_path = None
        self.regions = []  # Lista de dicts con config por región
        self.current_region_idx = -1
        self.results = {}  # region_idx -> result_image
        
        self.setup_style()
        self.create_widgets()
        self.show_step(1)
        
    def setup_style(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        self.bg_color = '#1a1a2e'
        fg_color = '#eaeaea'
        accent_color = '#e94560'
        
        self.root.configure(bg=self.bg_color)
        
        style.configure('TFrame', background=self.bg_color)
        style.configure('TLabel', background=self.bg_color, foreground=fg_color, font=('Segoe UI', 10))
        style.configure('Title.TLabel', font=('Segoe UI', 12, 'bold'), foreground=accent_color)
        style.configure('Step.TLabel', font=('Segoe UI', 11, 'bold'), foreground='#00ff88')
        style.configure('Info.TLabel', font=('Segoe UI', 9), foreground='#888888')
        style.configure('TButton', font=('Segoe UI', 10), padding=5)
        style.configure('Accent.TButton', font=('Segoe UI', 10, 'bold'))
        style.configure('TCheckbutton', background=self.bg_color, foreground=fg_color)
        style.configure('TRadiobutton', background=self.bg_color, foreground=fg_color)
        style.configure('TLabelframe', background=self.bg_color, foreground=fg_color)
        style.configure('TLabelframe.Label', background=self.bg_color, foreground=accent_color, font=('Segoe UI', 9, 'bold'))
        
    def create_widgets(self):
        # Header
        header = ttk.Frame(self.root)
        header.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(header, text="🎨 Pixel Art Transformer", style='Title.TLabel').pack(side=tk.LEFT)
        
        self.step_label = ttk.Label(header, text="Paso 1: Cargar imagen", style='Step.TLabel')
        self.step_label.pack(side=tk.RIGHT)
        
        # Main container
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Step 1: Load image
        self.step1_frame = ttk.Frame(self.main_container)
        self.create_step1()
        
        # Step 2: Select regions
        self.step2_frame = ttk.Frame(self.main_container)
        self.create_step2()
        
        # Step 3: Edit regions
        self.step3_frame = ttk.Frame(self.main_container)
        self.create_step3()
        
        # Step 4: Generate
        self.step4_frame = ttk.Frame(self.main_container)
        self.create_step4()
        
    def create_step1(self):
        """Paso 1: Cargar imagen"""
        center = ttk.Frame(self.step1_frame)
        center.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        ttk.Label(center, text="Arrastra una imagen o haz click para cargar", 
                 style='Info.TLabel').pack(pady=10)
        
        load_btn = ttk.Button(center, text="📂 Cargar Imagen", command=self.load_image, 
                             style='Accent.TButton')
        load_btn.pack(pady=10)
        
        self.load_info = ttk.Label(center, text="", style='Info.TLabel')
        self.load_info.pack()
        
    def create_step2(self):
        """Paso 2: Seleccionar regiones"""
        # Panel izquierdo - controles
        left = ttk.Frame(self.step2_frame, width=200)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        left.pack_propagate(False)
        
        ttk.Label(left, text="Selecciona las figuras", style='Title.TLabel').pack(pady=5)
        ttk.Label(left, text="Dibuja rectángulos sobre\ncada sprite o figura", 
                 style='Info.TLabel').pack(pady=5)
        
        self.regions_list = tk.Listbox(left, bg='#16213e', fg='#eaeaea', height=8,
                                       selectbackground='#e94560')
        self.regions_list.pack(fill=tk.X, padx=5, pady=5)
        
        btn_frame = ttk.Frame(left)
        btn_frame.pack(fill=tk.X, padx=5)
        
        ttk.Button(btn_frame, text="🗑️ Eliminar", command=self.remove_selected_region).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="🧹 Limpiar", command=self.clear_all_regions).pack(side=tk.RIGHT)
        
        ttk.Separator(left, orient='horizontal').pack(fill=tk.X, pady=10)
        
        nav_frame = ttk.Frame(left)
        nav_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(nav_frame, text="← Atrás", command=lambda: self.show_step(1)).pack(side=tk.LEFT)
        self.step2_next = ttk.Button(nav_frame, text="Continuar →", command=self.go_to_step3,
                                     style='Accent.TButton')
        self.step2_next.pack(side=tk.RIGHT)
        
        # Canvas principal
        self.region_canvas = RegionSelectCanvas(self.step2_frame, bg='#0f0f23', 
                                                highlightthickness=0,
                                                on_region_added=self.on_region_added)
        self.region_canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
    def create_step3(self):
        """Paso 3: Editar cada región"""
        # Panel izquierdo - controles
        left = ttk.Frame(self.step3_frame, width=220)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        left.pack_propagate(False)
        
        # Navegación entre regiones
        nav_region = ttk.Frame(left)
        nav_region.pack(fill=tk.X, padx=5, pady=5)
        
        self.prev_region_btn = ttk.Button(nav_region, text="◀", width=3, command=self.prev_region)
        self.prev_region_btn.pack(side=tk.LEFT)
        
        self.region_indicator = ttk.Label(nav_region, text="Región 1/1", style='Title.TLabel')
        self.region_indicator.pack(side=tk.LEFT, expand=True)
        
        self.next_region_btn = ttk.Button(nav_region, text="▶", width=3, command=self.next_region)
        self.next_region_btn.pack(side=tk.RIGHT)
        
        ttk.Separator(left, orient='horizontal').pack(fill=tk.X, pady=5)
        
        # Grid size
        grid_frame = ttk.LabelFrame(left, text="📐 Grid", padding=5)
        grid_frame.pack(fill=tk.X, padx=5, pady=3)
        
        self.auto_detect = tk.BooleanVar(value=True)
        ttk.Checkbutton(grid_frame, text="Auto-detectar", variable=self.auto_detect,
                       command=self.update_region_preview).pack(anchor=tk.W)
        
        size_frame = ttk.Frame(grid_frame)
        size_frame.pack(fill=tk.X)
        ttk.Label(size_frame, text="Tamaño:").pack(side=tk.LEFT)
        self.grid_size = tk.IntVar(value=16)
        self.grid_spin = ttk.Spinbox(size_frame, from_=2, to=64, width=4,
                                     textvariable=self.grid_size, command=self.update_region_preview)
        self.grid_spin.pack(side=tk.RIGHT)
        
        # Offset
        offset_frame = ttk.LabelFrame(left, text="↔️ Offset", padding=5)
        offset_frame.pack(fill=tk.X, padx=5, pady=3)
        
        off_row = ttk.Frame(offset_frame)
        off_row.pack(fill=tk.X)
        ttk.Label(off_row, text="X:").pack(side=tk.LEFT)
        self.offset_x = tk.IntVar(value=0)
        ttk.Spinbox(off_row, from_=-32, to=32, width=4, textvariable=self.offset_x,
                   command=self.update_region_preview).pack(side=tk.LEFT, padx=2)
        ttk.Label(off_row, text="Y:").pack(side=tk.LEFT)
        self.offset_y = tk.IntVar(value=0)
        ttk.Spinbox(off_row, from_=-32, to=32, width=4, textvariable=self.offset_y,
                   command=self.update_region_preview).pack(side=tk.LEFT)
        
        # Bit depth
        bits_frame = ttk.LabelFrame(left, text="🎨 Colores", padding=5)
        bits_frame.pack(fill=tk.X, padx=5, pady=3)
        
        self.bits = tk.IntVar(value=8)
        bits_options = [("8-bit", 8), ("6-bit", 6), ("4-bit", 4), ("3-bit", 3)]
        for txt, val in bits_options:
            ttk.Radiobutton(bits_frame, text=txt, value=val, variable=self.bits,
                           command=self.update_region_preview).pack(side=tk.LEFT)
        
        # Excluir colores
        exc_frame = ttk.LabelFrame(left, text="🚫 Excluir", padding=5)
        exc_frame.pack(fill=tk.X, padx=5, pady=3)
        
        color_row = ttk.Frame(exc_frame)
        color_row.pack(fill=tk.X)
        
        self.exc_color1 = tk.Frame(color_row, bg='#333', width=25, height=20, relief=tk.RAISED, bd=1)
        self.exc_color1.pack(side=tk.LEFT, padx=2)
        self.exc_color1.bind('<Button-1>', lambda e: self.pick_exclude_color(0))
        
        self.exc_color2 = tk.Frame(color_row, bg='#333', width=25, height=20, relief=tk.RAISED, bd=1)
        self.exc_color2.pack(side=tk.LEFT, padx=2)
        self.exc_color2.bind('<Button-1>', lambda e: self.pick_exclude_color(1))
        
        ttk.Button(color_row, text="✕", width=2, command=self.clear_exclude_colors).pack(side=tk.LEFT, padx=5)
        
        tol_row = ttk.Frame(exc_frame)
        tol_row.pack(fill=tk.X, pady=3)
        ttk.Label(tol_row, text="Tolerancia:").pack(side=tk.LEFT)
        self.tolerance = tk.IntVar(value=10)
        ttk.Scale(tol_row, from_=0, to=50, variable=self.tolerance, orient=tk.HORIZONTAL,
                 command=lambda v: self.update_region_preview()).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.excluded_colors = [None, None]
        
        # Visualización
        viz_frame = ttk.Frame(left)
        viz_frame.pack(fill=tk.X, padx=5, pady=3)
        
        self.show_grid = tk.BooleanVar(value=True)
        ttk.Checkbutton(viz_frame, text="Grid", variable=self.show_grid,
                       command=self.update_region_preview).pack(side=tk.LEFT)
        self.show_centers = tk.BooleanVar(value=True)
        ttk.Checkbutton(viz_frame, text="Centros", variable=self.show_centers,
                       command=self.update_region_preview).pack(side=tk.LEFT)
        
        ttk.Separator(left, orient='horizontal').pack(fill=tk.X, pady=5)
        
        # Navegación principal
        nav_frame = ttk.Frame(left)
        nav_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(nav_frame, text="← Regiones", command=lambda: self.show_step(2)).pack(side=tk.LEFT)
        self.step3_next = ttk.Button(nav_frame, text="Generar →", command=self.generate_all,
                                     style='Accent.TButton')
        self.step3_next.pack(side=tk.RIGHT)
        
        # Canvas
        self.editor_canvas = RegionEditorCanvas(self.step3_frame, bg='#0f0f23', highlightthickness=0)
        self.editor_canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
    def create_step4(self):
        """Paso 4: Resultado final"""
        # Panel izquierdo
        left = ttk.Frame(self.step4_frame, width=200)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        left.pack_propagate(False)
        
        ttk.Label(left, text="✅ Completado", style='Title.TLabel').pack(pady=10)
        
        self.result_info = ttk.Label(left, text="", style='Info.TLabel', wraplength=180)
        self.result_info.pack(pady=5)
        
        ttk.Button(left, text="💾 Guardar Todo", command=self.save_all_results,
                  style='Accent.TButton').pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(left, text="💾 Guardar Seleccionado", command=self.save_selected).pack(fill=tk.X, padx=5)
        
        ttk.Separator(left, orient='horizontal').pack(fill=tk.X, pady=10)
        
        self.result_list = tk.Listbox(left, bg='#16213e', fg='#eaeaea', height=10,
                                      selectbackground='#e94560')
        self.result_list.pack(fill=tk.BOTH, expand=True, padx=5)
        self.result_list.bind('<<ListboxSelect>>', self.on_result_select)
        
        ttk.Separator(left, orient='horizontal').pack(fill=tk.X, pady=10)
        
        ttk.Button(left, text="← Editar regiones", command=lambda: self.show_step(3)).pack(fill=tk.X, padx=5)
        ttk.Button(left, text="🔄 Nueva imagen", command=lambda: self.show_step(1)).pack(fill=tk.X, padx=5, pady=5)
        
        # Canvas resultado
        self.result_canvas = RegionEditorCanvas(self.step4_frame, bg='#0f0f23', highlightthickness=0)
        self.result_canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
    def show_step(self, step):
        """Muestra el paso indicado."""
        for frame in [self.step1_frame, self.step2_frame, self.step3_frame, self.step4_frame]:
            frame.pack_forget()
            
        steps = {
            1: (self.step1_frame, "Paso 1: Cargar imagen"),
            2: (self.step2_frame, "Paso 2: Seleccionar regiones"),
            3: (self.step3_frame, "Paso 3: Configurar regiones"),
            4: (self.step4_frame, "Paso 4: Resultado"),
        }
        
        frame, label = steps[step]
        frame.pack(fill=tk.BOTH, expand=True)
        self.step_label.config(text=label)
        
    def load_image(self):
        filetypes = [("Imágenes", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"), ("Todos", "*.*")]
        filepath = filedialog.askopenfilename(title="Seleccionar imagen", filetypes=filetypes)
        
        if filepath:
            try:
                self.original_path = Path(filepath)
                self.original_image = Image.open(filepath)
                if self.original_image.mode != 'RGBA':
                    self.original_image = self.original_image.convert('RGBA')
                    
                self.load_info.config(text=f"✅ {self.original_path.name}\n{self.original_image.size[0]}×{self.original_image.size[1]}")
                
                # Preparar paso 2
                self.region_canvas.set_image(self.original_image)
                self.regions = []
                self.results = {}
                
                self.show_step(2)
                
            except Exception as e:
                messagebox.showerror("Error", str(e))
                
    def on_region_added(self, idx, coords):
        """Callback cuando se añade una región."""
        self.regions.append({
            'coords': coords,
            'grid_size': 16,
            'auto_detect': True,
            'offset_x': 0,
            'offset_y': 0,
            'bits': 8,
            'excluded_colors': [None, None],
            'tolerance': 10,
        })
        self.update_regions_list()
        
    def update_regions_list(self):
        self.regions_list.delete(0, tk.END)
        for i, region in enumerate(self.regions):
            x1, y1, x2, y2 = region['coords']
            self.regions_list.insert(tk.END, f"Región {i+1}: {x2-x1}×{y2-y1}")
            
    def remove_selected_region(self):
        sel = self.regions_list.curselection()
        if sel:
            idx = sel[0]
            del self.regions[idx]
            self.region_canvas.remove_region(idx)
            self.update_regions_list()
            
    def clear_all_regions(self):
        self.regions = []
        self.region_canvas.clear_regions()
        self.update_regions_list()
        
    def go_to_step3(self):
        if not self.regions:
            messagebox.showwarning("Aviso", "Selecciona al menos una región")
            return
        self.current_region_idx = 0
        self.load_current_region()
        self.show_step(3)
        
    def load_current_region(self):
        """Carga la región actual en el editor."""
        if not self.regions:
            return
            
        region = self.regions[self.current_region_idx]
        x1, y1, x2, y2 = region['coords']
        
        # Extraer subimagen
        self.current_region_image = self.original_image.crop((x1, y1, x2, y2))
        
        # Cargar configuración
        self.auto_detect.set(region['auto_detect'])
        self.grid_size.set(region['grid_size'])
        self.offset_x.set(region['offset_x'])
        self.offset_y.set(region['offset_y'])
        self.bits.set(region['bits'])
        self.tolerance.set(region['tolerance'])
        self.excluded_colors = region['excluded_colors'].copy()
        
        # Actualizar visual de colores
        for i, color in enumerate(self.excluded_colors):
            frame = self.exc_color1 if i == 0 else self.exc_color2
            if color:
                frame.config(bg='#{:02x}{:02x}{:02x}'.format(*color))
            else:
                frame.config(bg='#333')
        
        # Auto-detectar grid si es necesario
        if region['auto_detect']:
            detected = self.detect_grid_size(self.current_region_image)
            self.grid_size.set(detected)
        
        self.update_region_indicator()
        self.update_region_preview()
        
    def save_current_region_config(self):
        """Guarda la configuración actual de la región."""
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
        })
        
    def update_region_indicator(self):
        self.region_indicator.config(text=f"Región {self.current_region_idx + 1}/{len(self.regions)}")
        self.prev_region_btn.state(['!disabled'] if self.current_region_idx > 0 else ['disabled'])
        self.next_region_btn.state(['!disabled'] if self.current_region_idx < len(self.regions) - 1 else ['disabled'])
        
    def prev_region(self):
        self.save_current_region_config()
        if self.current_region_idx > 0:
            self.current_region_idx -= 1
            self.load_current_region()
            
    def next_region(self):
        self.save_current_region_config()
        if self.current_region_idx < len(self.regions) - 1:
            self.current_region_idx += 1
            self.load_current_region()
            
    def pick_exclude_color(self, idx):
        """Activa eyedropper para elegir color a excluir."""
        self.editor_canvas.enable_eyedropper(lambda c: self.set_exclude_color(idx, c))
        
    def set_exclude_color(self, idx, color):
        self.excluded_colors[idx] = color
        frame = self.exc_color1 if idx == 0 else self.exc_color2
        frame.config(bg='#{:02x}{:02x}{:02x}'.format(*color))
        self.update_region_preview()
        
    def clear_exclude_colors(self):
        self.excluded_colors = [None, None]
        self.exc_color1.config(bg='#333')
        self.exc_color2.config(bg='#333')
        self.update_region_preview()
        
    def detect_grid_size(self, image):
        """Detecta el tamaño del grid."""
        img_array = np.array(image.convert('RGB'))
        width, height = image.size
        
        for size in [64, 48, 32, 24, 16, 12, 10, 8, 6, 5, 4, 3, 2]:
            if width % size != 0 or height % size != 0:
                continue
            blocks_x = width // size
            blocks_y = height // size
            uniform = 0
            total = 0
            for i in range(min(50, blocks_x * blocks_y)):
                bx = (i % blocks_x) * size
                by = (i // blocks_x) * size
                block = img_array[by:by+size, bx:bx+size]
                if np.all(block == block[0, 0]):
                    uniform += 1
                total += 1
            if total > 0 and uniform / total >= 0.9:
                return size
        return 16
        
    def update_region_preview(self):
        """Actualiza la preview de la región actual."""
        if not hasattr(self, 'current_region_image') or self.current_region_image is None:
            return
            
        cell_size = self.grid_size.get()
        offset_x = self.offset_x.get()
        offset_y = self.offset_y.get()
        
        image = self.current_region_image.copy()
        
        if self.show_grid.get() or self.show_centers.get():
            image = self.draw_grid_overlay(image, cell_size, offset_x, offset_y)
        
        self.editor_canvas.set_image(image)
        
    def reduce_color(self, color, bits):
        if bits >= 8:
            return color
        levels = 2 ** bits
        factor = 256 // levels
        return tuple(min(255, (c // factor) * factor + factor // 2) for c in color[:3])
        
    def colors_similar(self, c1, c2, tol):
        return all(abs(a - b) <= tol for a, b in zip(c1, c2))
        
    def draw_grid_overlay(self, image, cell_size, offset_x, offset_y):
        if image.mode != 'RGBA':
            viz = image.convert('RGBA')
        else:
            viz = image.copy()
            
        overlay = Image.new('RGBA', viz.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        width, height = image.size
        
        if self.show_grid.get():
            grid_color = (255, 50, 80, 150)
            for x in range(offset_x, width + 1, cell_size):
                if x >= 0:
                    draw.line([(x, 0), (x, height)], fill=grid_color, width=1)
            for y in range(offset_y, height + 1, cell_size):
                if y >= 0:
                    draw.line([(0, y), (width, y)], fill=grid_color, width=1)
        
        if self.show_centers.get():
            bits = self.bits.get()
            tol = self.tolerance.get()
            marker_size = max(1, cell_size // 8)
            start_x = offset_x if offset_x >= 0 else offset_x % cell_size
            start_y = offset_y if offset_y >= 0 else offset_y % cell_size
            
            for y in range(start_y, height, cell_size):
                for x in range(start_x, width, cell_size):
                    cx = x + cell_size // 2
                    cy = y + cell_size // 2
                    if 0 <= cx < width and 0 <= cy < height:
                        pixel = image.getpixel((cx, cy))[:3]
                        reduced = self.reduce_color(pixel, bits)
                        
                        excluded = any(
                            self.colors_similar(reduced, exc, tol)
                            for exc in self.excluded_colors if exc
                        )
                        
                        if excluded:
                            draw.line([(cx-marker_size, cy-marker_size), (cx+marker_size, cy+marker_size)],
                                     fill=(255, 100, 100, 200), width=2)
                            draw.line([(cx+marker_size, cy-marker_size), (cx-marker_size, cy+marker_size)],
                                     fill=(255, 100, 100, 200), width=2)
                        else:
                            draw.ellipse([(cx-marker_size, cy-marker_size), (cx+marker_size, cy+marker_size)],
                                        fill=(50, 255, 100, 200))
        
        return Image.alpha_composite(viz, overlay)
        
    def generate_all(self):
        """Genera todas las regiones."""
        self.save_current_region_config()
        self.results = {}
        
        for idx, region in enumerate(self.regions):
            x1, y1, x2, y2 = region['coords']
            img = self.original_image.crop((x1, y1, x2, y2))
            
            cell_size = region['grid_size']
            offset_x = region['offset_x']
            offset_y = region['offset_y']
            bits = region['bits']
            excluded = [c for c in region['excluded_colors'] if c]
            tol = region['tolerance']
            
            start_x = offset_x if offset_x >= 0 else offset_x % cell_size
            start_y = offset_y if offset_y >= 0 else offset_y % cell_size
            
            new_w = (img.size[0] - start_x) // cell_size
            new_h = (img.size[1] - start_y) // cell_size
            
            if new_w < 1 or new_h < 1:
                continue
                
            result = Image.new('RGBA', (new_w, new_h), (0, 0, 0, 0))
            
            for py in range(new_h):
                for px in range(new_w):
                    cx = start_x + px * cell_size + cell_size // 2
                    cy = start_y + py * cell_size + cell_size // 2
                    cx = min(cx, img.size[0] - 1)
                    cy = min(cy, img.size[1] - 1)
                    
                    color = img.getpixel((cx, cy))
                    if len(color) == 3:
                        color = color + (255,)
                        
                    rgb = self.reduce_color(color[:3], bits)
                    
                    is_excluded = any(self.colors_similar(rgb, exc, tol) for exc in excluded)
                    
                    if is_excluded:
                        result.putpixel((px, py), (0, 0, 0, 0))
                    else:
                        result.putpixel((px, py), rgb + (color[3],))
            
            self.results[idx] = result
        
        # Mostrar resultados
        self.result_list.delete(0, tk.END)
        for idx in self.results:
            r = self.results[idx]
            self.result_list.insert(tk.END, f"Región {idx+1}: {r.size[0]}×{r.size[1]}")
            
        self.result_info.config(text=f"✅ {len(self.results)} regiones generadas")
        
        if self.results:
            self.result_list.selection_set(0)
            self.result_canvas.set_image(self.results[0])
            
        self.show_step(4)
        
    def on_result_select(self, event):
        sel = self.result_list.curselection()
        if sel:
            idx = sel[0]
            if idx in self.results:
                self.result_canvas.set_image(self.results[idx])
                
    def save_all_results(self):
        if not self.results:
            return
        folder = filedialog.askdirectory(title="Seleccionar carpeta")
        if folder:
            for idx, img in self.results.items():
                name = f"{self.original_path.stem}_region{idx+1}.png"
                img.save(Path(folder) / name, 'PNG')
            messagebox.showinfo("Guardado", f"{len(self.results)} imágenes guardadas en:\n{folder}")
            
    def save_selected(self):
        sel = self.result_list.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx not in self.results:
            return
        default_name = f"{self.original_path.stem}_region{idx+1}.png"
        filepath = filedialog.asksaveasfilename(
            title="Guardar", defaultextension=".png",
            initialfile=default_name, filetypes=[("PNG", "*.png")]
        )
        if filepath:
            self.results[idx].save(filepath, 'PNG')
            messagebox.showinfo("Guardado", f"Imagen guardada:\n{filepath}")


def main():
    root = tk.Tk()
    app = PixelArtTransformerGUI(root)
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f'+{x}+{y}')
    root.mainloop()


if __name__ == '__main__':
    main()
