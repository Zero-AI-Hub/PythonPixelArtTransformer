"""
Pixel Art Transformer - Interfaz Gráfica v3
============================================
Aplicación con GUI para convertir imágenes de pixel art escaladas
a su forma real (1 pixel por pixel).

Características:
- Zoom con rueda del ratón
- Pan/arrastrar con click izquierdo
- Exclusión de colores de fondo (hasta 2 colores)
- Selección de color directamente desde la imagen (eyedropper)
- Ajuste de offset del grid para alinear píxeles desplazados
- Vista previa del grid en tiempo real
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from PIL import Image, ImageTk, ImageDraw
import numpy as np
from pathlib import Path


class ZoomableCanvas(tk.Canvas):
    """Canvas con soporte para zoom, pan y eyedropper."""
    
    def __init__(self, parent, on_color_pick=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.image = None
        self.original_image = None  # Imagen sin grid overlay
        self.photo = None
        self.image_id = None
        self.on_color_pick = on_color_pick
        
        # Zoom y pan
        self.zoom_level = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 20.0
        self.offset_x = 0
        self.offset_y = 0
        
        # Para arrastrar
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.dragging = False
        
        # Modo eyedropper
        self.eyedropper_mode = False
        self.eyedropper_callback = None
        
        # Bindings
        self.bind('<MouseWheel>', self.on_mousewheel)
        self.bind('<Button-4>', self.on_mousewheel)  # Linux scroll up
        self.bind('<Button-5>', self.on_mousewheel)  # Linux scroll down
        self.bind('<ButtonPress-1>', self.on_click)
        self.bind('<B1-Motion>', self.on_drag)
        self.bind('<ButtonRelease-1>', self.on_drag_end)
        self.bind('<Configure>', self.on_resize)
        self.bind('<Motion>', self.on_mouse_move)
        
    def set_image(self, image, original=None):
        """Establece la imagen a mostrar."""
        self.image = image
        self.original_image = original if original else image
        self.reset_view()
        self.redraw()
        
    def reset_view(self):
        """Resetea zoom y posición."""
        if self.image is None:
            return
            
        self.update_idletasks()
        canvas_w = self.winfo_width()
        canvas_h = self.winfo_height()
        
        if canvas_w < 10 or canvas_h < 10:
            self.zoom_level = 1.0
        else:
            img_w, img_h = self.image.size
            scale_x = canvas_w / img_w
            scale_y = canvas_h / img_h
            self.zoom_level = min(scale_x, scale_y, 4.0)
        
        self.offset_x = 0
        self.offset_y = 0
        
    def redraw(self):
        """Redibuja la imagen con el zoom y offset actuales."""
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
        self.img_w = new_w
        self.img_h = new_h
        
        self.image_id = self.create_image(self.img_x, self.img_y, anchor=tk.NW, image=self.photo)
        
        # Mostrar nivel de zoom y modo
        zoom_pct = int(self.zoom_level * 100)
        mode_text = " [🎯 EYEDROPPER]" if self.eyedropper_mode else ""
        self.create_text(10, 10, text=f"Zoom: {zoom_pct}%{mode_text}", 
                        fill='#00ff88', anchor=tk.NW, font=('Segoe UI', 9))
        
    def enable_eyedropper(self, callback):
        """Activa el modo eyedropper."""
        self.eyedropper_mode = True
        self.eyedropper_callback = callback
        self.config(cursor='crosshair')
        self.redraw()
        
    def disable_eyedropper(self):
        """Desactiva el modo eyedropper."""
        self.eyedropper_mode = False
        self.eyedropper_callback = None
        self.config(cursor='')
        self.redraw()
        
    def screen_to_image_coords(self, screen_x, screen_y):
        """Convierte coordenadas de pantalla a coordenadas de imagen."""
        if self.image is None:
            return None, None
            
        # Posición relativa a la imagen mostrada
        rel_x = screen_x - self.img_x
        rel_y = screen_y - self.img_y
        
        # Escalar a coordenadas de imagen original
        img_x = int(rel_x / self.zoom_level)
        img_y = int(rel_y / self.zoom_level)
        
        # Verificar límites
        img_w, img_h = self.original_image.size
        if 0 <= img_x < img_w and 0 <= img_y < img_h:
            return img_x, img_y
        return None, None
        
    def on_mouse_move(self, event):
        """Muestra información del pixel bajo el cursor."""
        if self.eyedropper_mode and self.original_image:
            img_x, img_y = self.screen_to_image_coords(event.x, event.y)
            if img_x is not None:
                color = self.original_image.getpixel((img_x, img_y))[:3]
                # Mostrar preview del color en algún lado si queremos
        
    def on_click(self, event):
        """Maneja click - eyedropper o inicio de arrastre."""
        if self.eyedropper_mode and self.original_image:
            img_x, img_y = self.screen_to_image_coords(event.x, event.y)
            if img_x is not None:
                color = self.original_image.getpixel((img_x, img_y))[:3]
                if self.eyedropper_callback:
                    self.eyedropper_callback(color)
                self.disable_eyedropper()
                return
        
        # Modo normal: iniciar arrastre
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.dragging = True
        self.config(cursor='fleur')
        
    def on_mousewheel(self, event):
        """Maneja el zoom con la rueda del ratón."""
        if self.image is None:
            return
            
        if event.num == 4 or event.delta > 0:
            factor = 1.2
        else:
            factor = 0.8
            
        new_zoom = self.zoom_level * factor
        new_zoom = max(self.min_zoom, min(self.max_zoom, new_zoom))
        
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
        
    def on_drag(self, event):
        """Arrastra la imagen."""
        if not self.dragging or self.eyedropper_mode:
            return
            
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y
        
        self.offset_x += dx
        self.offset_y += dy
        
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        
        self.redraw()
        
    def on_drag_end(self, event):
        """Termina el arrastre."""
        self.dragging = False
        if not self.eyedropper_mode:
            self.config(cursor='')
        
    def on_resize(self, event):
        """Redibuja al cambiar tamaño."""
        if self.image is not None:
            self.redraw()


class ColorExclusionFrame(ttk.LabelFrame):
    """Frame para seleccionar colores a excluir con soporte para eyedropper."""
    
    def __init__(self, parent, on_change_callback=None, get_canvas_callback=None, **kwargs):
        super().__init__(parent, text="🚫 Excluir Colores", **kwargs)
        
        self.on_change = on_change_callback
        self.get_canvas = get_canvas_callback
        self.excluded_colors = []
        self.pending_color_index = None
        
        self.create_widgets()
        
    def create_widgets(self):
        """Crea los widgets del frame."""
        ttk.Label(self, text="Click derecho: selector | Click izq: de imagen", 
                 style='Info.TLabel').pack(anchor=tk.W, pady=(0, 5))
        
        colors_frame = ttk.Frame(self)
        colors_frame.pack(fill=tk.X)
        
        # Color 1
        self.color1_frame = tk.Frame(colors_frame, bg='#333333', width=40, height=30,
                                     relief=tk.RAISED, bd=2)
        self.color1_frame.pack(side=tk.LEFT, padx=(0, 5))
        self.color1_frame.bind('<Button-1>', lambda e: self.start_eyedropper(0))
        self.color1_frame.bind('<Button-3>', lambda e: self.pick_color_dialog(0))
        self.color1_frame.pack_propagate(False)
        self.color1_label = tk.Label(self.color1_frame, text="+", fg='#888888', bg='#333333')
        self.color1_label.pack(expand=True)
        self.color1_label.bind('<Button-1>', lambda e: self.start_eyedropper(0))
        self.color1_label.bind('<Button-3>', lambda e: self.pick_color_dialog(0))
        
        # Color 2
        self.color2_frame = tk.Frame(colors_frame, bg='#333333', width=40, height=30,
                                     relief=tk.RAISED, bd=2)
        self.color2_frame.pack(side=tk.LEFT, padx=(0, 5))
        self.color2_frame.bind('<Button-1>', lambda e: self.start_eyedropper(1))
        self.color2_frame.bind('<Button-3>', lambda e: self.pick_color_dialog(1))
        self.color2_frame.pack_propagate(False)
        self.color2_label = tk.Label(self.color2_frame, text="+", fg='#888888', bg='#333333')
        self.color2_label.pack(expand=True)
        self.color2_label.bind('<Button-1>', lambda e: self.start_eyedropper(1))
        self.color2_label.bind('<Button-3>', lambda e: self.pick_color_dialog(1))
        
        self.color_frames = [self.color1_frame, self.color2_frame]
        self.color_labels = [self.color1_label, self.color2_label]
        
        # Botón limpiar
        clear_btn = ttk.Button(colors_frame, text="✕", width=3, 
                              command=self.clear_colors)
        clear_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Info
        self.info_label = ttk.Label(self, text="Sin colores excluídos", style='Info.TLabel')
        self.info_label.pack(anchor=tk.W, pady=(5, 0))
        
    def start_eyedropper(self, index):
        """Inicia el modo eyedropper para seleccionar color de la imagen."""
        if self.get_canvas:
            canvas = self.get_canvas()
            if canvas and canvas.original_image:
                self.pending_color_index = index
                canvas.enable_eyedropper(self.on_eyedropper_pick)
                self.info_label.config(text="🎯 Click en la imagen para seleccionar color...")
                
    def on_eyedropper_pick(self, rgb):
        """Callback cuando se selecciona un color con eyedropper."""
        if self.pending_color_index is not None:
            self.set_color(self.pending_color_index, rgb)
            self.pending_color_index = None
            
    def pick_color_dialog(self, index):
        """Abre el selector de color tradicional."""
        color = colorchooser.askcolor(title=f"Seleccionar color {index + 1} a excluir")
        if color[0]:
            rgb = tuple(int(c) for c in color[0])
            self.set_color(index, rgb)
            
    def set_color(self, index, rgb):
        """Establece un color en el índice dado."""
        if index < len(self.excluded_colors):
            self.excluded_colors[index] = rgb
        else:
            self.excluded_colors.append(rgb)
        
        hex_color = '#{:02x}{:02x}{:02x}'.format(*rgb)
        self.color_frames[index].config(bg=hex_color)
        self.color_labels[index].config(text="", bg=hex_color)
        
        self.update_info()
        
        if self.on_change:
            self.on_change()
                
    def clear_colors(self):
        """Limpia todos los colores."""
        self.excluded_colors = []
        for frame, label in zip(self.color_frames, self.color_labels):
            frame.config(bg='#333333')
            label.config(text="+", bg='#333333', fg='#888888')
        self.update_info()
        
        if self.on_change:
            self.on_change()
            
    def update_info(self):
        """Actualiza el texto informativo."""
        count = len(self.excluded_colors)
        if count == 0:
            self.info_label.config(text="Sin colores excluídos")
        else:
            self.info_label.config(text=f"{count} color(es) serán transparentes")
            
    def get_excluded_colors(self):
        """Retorna la lista de colores excluídos."""
        return self.excluded_colors.copy()


class PixelArtTransformerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎨 Pixel Art Transformer v3")
        self.root.geometry("1350x900")
        self.root.minsize(1100, 750)
        
        # Variables
        self.original_image = None
        self.original_path = None
        self.result_image = None
        self.grid_image = None
        self.preview_image = None
        self.detected_size = tk.IntVar(value=0)
        self.manual_size = tk.IntVar(value=16)
        self.use_auto_detect = tk.BooleanVar(value=True)
        self.show_grid_overlay = tk.BooleanVar(value=True)
        self.show_center_markers = tk.BooleanVar(value=True)
        
        # Grid offset
        self.grid_offset_x = tk.IntVar(value=0)
        self.grid_offset_y = tk.IntVar(value=0)
        
        # Estilo
        self.setup_style()
        
        # Layout principal
        self.create_widgets()
        
    def setup_style(self):
        """Configura el estilo visual de la aplicación."""
        style = ttk.Style()
        style.theme_use('clam')
        
        self.bg_color = '#1a1a2e'
        fg_color = '#eaeaea'
        accent_color = '#e94560'
        
        self.root.configure(bg=self.bg_color)
        
        style.configure('TFrame', background=self.bg_color)
        style.configure('TLabel', background=self.bg_color, foreground=fg_color, font=('Segoe UI', 10))
        style.configure('Title.TLabel', font=('Segoe UI', 14, 'bold'), foreground=accent_color)
        style.configure('Info.TLabel', font=('Segoe UI', 9), foreground='#888888')
        style.configure('TButton', font=('Segoe UI', 10), padding=8)
        style.configure('Accent.TButton', font=('Segoe UI', 11, 'bold'))
        style.configure('TCheckbutton', background=self.bg_color, foreground=fg_color)
        style.configure('TRadiobutton', background=self.bg_color, foreground=fg_color)
        style.configure('TScale', background=self.bg_color)
        style.configure('TSpinbox', font=('Segoe UI', 10))
        style.configure('TLabelframe', background=self.bg_color, foreground=fg_color)
        style.configure('TLabelframe.Label', background=self.bg_color, foreground=accent_color, font=('Segoe UI', 10, 'bold'))
        
    def create_widgets(self):
        """Crea todos los widgets de la interfaz."""
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        left_panel = ttk.Frame(main_frame, width=340)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.create_control_panel(left_panel)
        self.create_preview_panel(right_panel)
        
    def create_control_panel(self, parent):
        """Crea el panel de controles."""
        canvas = tk.Canvas(parent, bg=self.bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=320)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Título
        title = ttk.Label(scrollable_frame, text="🎨 Pixel Art Transformer", style='Title.TLabel')
        title.pack(pady=(0, 15))
        
        # --- Sección: Cargar imagen ---
        load_frame = ttk.LabelFrame(scrollable_frame, text="📂 Imagen", padding=10)
        load_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.load_btn = ttk.Button(load_frame, text="Cargar Imagen", command=self.load_image)
        self.load_btn.pack(fill=tk.X)
        
        self.file_label = ttk.Label(load_frame, text="Ningún archivo seleccionado", style='Info.TLabel', wraplength=280)
        self.file_label.pack(pady=(5, 0))
        
        self.size_label = ttk.Label(load_frame, text="", style='Info.TLabel')
        self.size_label.pack()
        
        # --- Sección: Configuración del Grid ---
        grid_frame = ttk.LabelFrame(scrollable_frame, text="📐 Tamaño del Grid", padding=10)
        grid_frame.pack(fill=tk.X, pady=(0, 10))
        
        auto_radio = ttk.Radiobutton(
            grid_frame, text="Auto-detectar", 
            variable=self.use_auto_detect, value=True,
            command=self.on_grid_mode_change
        )
        auto_radio.pack(anchor=tk.W)
        
        self.auto_result_label = ttk.Label(grid_frame, text="", style='Info.TLabel')
        self.auto_result_label.pack(anchor=tk.W, padx=(20, 0))
        
        manual_radio = ttk.Radiobutton(
            grid_frame, text="Manual:", 
            variable=self.use_auto_detect, value=False,
            command=self.on_grid_mode_change
        )
        manual_radio.pack(anchor=tk.W, pady=(10, 0))
        
        slider_frame = ttk.Frame(grid_frame)
        slider_frame.pack(fill=tk.X, padx=(20, 0))
        
        self.size_slider = ttk.Scale(
            slider_frame, from_=2, to=64, 
            variable=self.manual_size, orient=tk.HORIZONTAL,
            command=self.on_slider_change
        )
        self.size_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.size_value_label = ttk.Label(slider_frame, text="16x16", width=6)
        self.size_value_label.pack(side=tk.RIGHT)
        
        # --- Sección: Offset del Grid ---
        offset_frame = ttk.LabelFrame(scrollable_frame, text="↔️ Offset del Grid", padding=10)
        offset_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(offset_frame, text="Ajusta si los píxeles están desalineados:", 
                 style='Info.TLabel').pack(anchor=tk.W, pady=(0, 5))
        
        offset_controls = ttk.Frame(offset_frame)
        offset_controls.pack(fill=tk.X)
        
        # Offset X
        x_frame = ttk.Frame(offset_controls)
        x_frame.pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Label(x_frame, text="X:", width=3).pack(side=tk.LEFT)
        self.offset_x_spin = ttk.Spinbox(
            x_frame, from_=-32, to=32, width=5,
            textvariable=self.grid_offset_x,
            command=self.on_offset_change
        )
        self.offset_x_spin.pack(side=tk.LEFT, padx=(0, 10))
        self.offset_x_spin.bind('<Return>', lambda e: self.on_offset_change())
        self.offset_x_spin.bind('<FocusOut>', lambda e: self.on_offset_change())
        
        # Offset Y
        y_frame = ttk.Frame(offset_controls)
        y_frame.pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Label(y_frame, text="Y:", width=3).pack(side=tk.LEFT)
        self.offset_y_spin = ttk.Spinbox(
            y_frame, from_=-32, to=32, width=5,
            textvariable=self.grid_offset_y,
            command=self.on_offset_change
        )
        self.offset_y_spin.pack(side=tk.LEFT)
        self.offset_y_spin.bind('<Return>', lambda e: self.on_offset_change())
        self.offset_y_spin.bind('<FocusOut>', lambda e: self.on_offset_change())
        
        # Botón reset offset
        reset_offset_btn = ttk.Button(offset_controls, text="Reset", width=5,
                                      command=self.reset_offset)
        reset_offset_btn.pack(side=tk.RIGHT)
        
        # --- Sección: Exclusión de colores ---
        self.color_exclusion = ColorExclusionFrame(
            scrollable_frame, 
            on_change_callback=self.update_preview,
            get_canvas_callback=self.get_original_canvas,
            padding=10
        )
        self.color_exclusion.pack(fill=tk.X, pady=(0, 10))
        
        # --- Sección: Opciones de visualización ---
        viz_frame = ttk.LabelFrame(scrollable_frame, text="👁️ Visualización", padding=10)
        viz_frame.pack(fill=tk.X, pady=(0, 10))
        
        grid_check = ttk.Checkbutton(
            viz_frame, text="Mostrar grid",
            variable=self.show_grid_overlay,
            command=self.update_preview
        )
        grid_check.pack(anchor=tk.W)
        
        center_check = ttk.Checkbutton(
            viz_frame, text="Mostrar puntos centrales",
            variable=self.show_center_markers,
            command=self.update_preview
        )
        center_check.pack(anchor=tk.W)
        
        zoom_frame = ttk.Frame(viz_frame)
        zoom_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(zoom_frame, text="Zoom:", style='Info.TLabel').pack(side=tk.LEFT)
        
        reset_zoom_btn = ttk.Button(zoom_frame, text="Reset", width=6,
                                    command=self.reset_zoom)
        reset_zoom_btn.pack(side=tk.RIGHT)
        
        ttk.Label(viz_frame, text="Rueda: zoom | Arrastrar: mover", 
                 style='Info.TLabel').pack(anchor=tk.W, pady=(5, 0))
        
        # --- Sección: Acciones ---
        action_frame = ttk.LabelFrame(scrollable_frame, text="⚡ Acciones", padding=10)
        action_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.transform_btn = ttk.Button(
            action_frame, text="✨ Transformar", 
            command=self.transform_image, style='Accent.TButton'
        )
        self.transform_btn.pack(fill=tk.X, pady=(0, 5))
        self.transform_btn.state(['disabled'])
        
        self.save_btn = ttk.Button(
            action_frame, text="💾 Guardar Resultado",
            command=self.save_result
        )
        self.save_btn.pack(fill=tk.X, pady=(0, 5))
        self.save_btn.state(['disabled'])
        
        self.save_grid_btn = ttk.Button(
            action_frame, text="📏 Guardar Grid",
            command=self.save_grid
        )
        self.save_grid_btn.pack(fill=tk.X)
        self.save_grid_btn.state(['disabled'])
        
        # --- Info del resultado ---
        result_frame = ttk.LabelFrame(scrollable_frame, text="📊 Resultado", padding=10)
        result_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.result_info = ttk.Label(result_frame, text="Transforma una imagen para ver los resultados", style='Info.TLabel', wraplength=280)
        self.result_info.pack()
        
    def get_original_canvas(self):
        """Retorna el canvas original para el eyedropper."""
        return self.original_canvas
        
    def create_preview_panel(self, parent):
        """Crea el panel de vista previa con canvases con zoom."""
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Pestaña 1: Original con Grid
        self.original_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.original_tab, text="📷 Original + Grid")
        
        self.original_canvas = ZoomableCanvas(self.original_tab, bg='#0f0f23', highlightthickness=0)
        self.original_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Pestaña 2: Resultado
        self.result_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.result_tab, text="✨ Resultado")
        
        self.result_canvas = ZoomableCanvas(self.result_tab, bg='#0f0f23', highlightthickness=0)
        self.result_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Pestaña 3: Comparación
        self.compare_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.compare_tab, text="🔄 Comparar")
        
        compare_frame = ttk.Frame(self.compare_tab)
        compare_frame.pack(fill=tk.BOTH, expand=True)
        
        self.compare_left = ZoomableCanvas(compare_frame, bg='#0f0f23', highlightthickness=0)
        self.compare_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.compare_right = ZoomableCanvas(compare_frame, bg='#0f0f23', highlightthickness=0)
        self.compare_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
    def load_image(self):
        """Carga una imagen desde el sistema de archivos."""
        filetypes = [
            ("Imágenes", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
            ("PNG", "*.png"),
            ("JPEG", "*.jpg *.jpeg"),
            ("Todos los archivos", "*.*")
        ]
        
        filepath = filedialog.askopenfilename(
            title="Seleccionar imagen de pixel art",
            filetypes=filetypes
        )
        
        if filepath:
            try:
                self.original_path = Path(filepath)
                self.original_image = Image.open(filepath)
                
                if self.original_image.mode == 'P':
                    self.original_image = self.original_image.convert('RGBA')
                elif self.original_image.mode != 'RGBA':
                    self.original_image = self.original_image.convert('RGBA')
                
                self.file_label.config(text=self.original_path.name)
                self.size_label.config(text=f"Dimensiones: {self.original_image.size[0]}×{self.original_image.size[1]}")
                
                # Reset
                self.color_exclusion.clear_colors()
                self.grid_offset_x.set(0)
                self.grid_offset_y.set(0)
                
                self.detect_grid_size()
                self.transform_btn.state(['!disabled'])
                self.update_preview()
                
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cargar la imagen:\n{e}")
                
    def detect_grid_size(self):
        """Detecta automáticamente el tamaño del grid."""
        if self.original_image is None:
            return
            
        img_array = np.array(self.original_image.convert('RGB'))
        width, height = self.original_image.size
        
        common_sizes = [64, 48, 32, 24, 16, 12, 10, 8, 6, 5, 4, 3, 2]
        all_sizes = [s for s in range(128, 1, -1) if width % s == 0 and height % s == 0]
        
        sizes_to_check = [s for s in common_sizes if s in all_sizes]
        sizes_to_check.extend([s for s in all_sizes if s not in sizes_to_check])
        
        detected = 1
        
        for size in sizes_to_check:
            blocks_x = width // size
            blocks_y = height // size
            max_samples = min(100, blocks_x * blocks_y)
            step = max(1, (blocks_x * blocks_y) // max_samples)
            
            uniform_count = 0
            sample_count = 0
            
            for i in range(0, blocks_x * blocks_y, step):
                bx = (i % blocks_x) * size
                by = (i // blocks_x) * size
                
                block = img_array[by:by+size, bx:bx+size]
                first_pixel = block[0, 0]
                
                if np.all(block == first_pixel):
                    uniform_count += 1
                sample_count += 1
            
            if sample_count > 0 and uniform_count / sample_count >= 0.95:
                detected = size
                break
        
        self.detected_size.set(detected)
        result_w = width // detected
        result_h = height // detected
        self.auto_result_label.config(text=f"Detectado: {detected}×{detected} → {result_w}×{result_h} px")
        
    def on_grid_mode_change(self):
        """Callback cuando cambia el modo de grid."""
        self.update_preview()
        
    def on_slider_change(self, value):
        """Callback cuando cambia el slider."""
        size = int(float(value))
        self.size_value_label.config(text=f"{size}×{size}")
        if not self.use_auto_detect.get():
            self.update_preview()
            
    def on_offset_change(self):
        """Callback cuando cambia el offset del grid."""
        self.update_preview()
        
    def reset_offset(self):
        """Resetea el offset a 0,0."""
        self.grid_offset_x.set(0)
        self.grid_offset_y.set(0)
        self.update_preview()
            
    def get_current_grid_size(self):
        """Obtiene el tamaño de grid actual."""
        if self.use_auto_detect.get():
            return self.detected_size.get()
        return self.manual_size.get()
        
    def reset_zoom(self):
        """Resetea el zoom de todos los canvas."""
        self.original_canvas.reset_view()
        self.original_canvas.redraw()
        self.result_canvas.reset_view()
        self.result_canvas.redraw()
        self.compare_left.reset_view()
        self.compare_left.redraw()
        self.compare_right.reset_view()
        self.compare_right.redraw()
        
    def update_preview(self):
        """Actualiza la vista previa."""
        if self.original_image is None:
            return
            
        cell_size = self.get_current_grid_size()
        if cell_size < 2:
            return
            
        offset_x = self.grid_offset_x.get()
        offset_y = self.grid_offset_y.get()
            
        if self.show_grid_overlay.get():
            preview_img = self.create_grid_visualization(
                self.original_image, cell_size,
                self.show_center_markers.get(),
                offset_x, offset_y
            )
        else:
            preview_img = self.original_image.copy()
            
        self.preview_image = preview_img
        self.original_canvas.set_image(preview_img, self.original_image)
        
    def create_grid_visualization(self, image, cell_size, show_centers=True, offset_x=0, offset_y=0):
        """Crea visualización del grid con offset."""
        if image.mode != 'RGBA':
            viz_image = image.convert('RGBA')
        else:
            viz_image = image.copy()
        
        overlay = Image.new('RGBA', viz_image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        width, height = image.size
        grid_color = (255, 50, 80, 150)
        
        # Líneas verticales con offset
        for x in range(offset_x, width + 1, cell_size):
            if x >= 0:
                draw.line([(x, 0), (x, height)], fill=grid_color, width=1)
        
        # Líneas horizontales con offset
        for y in range(offset_y, height + 1, cell_size):
            if y >= 0:
                draw.line([(0, y), (width, y)], fill=grid_color, width=1)
        
        excluded = self.color_exclusion.get_excluded_colors()
        
        if show_centers:
            marker_size = max(1, cell_size // 8)
            
            # Calcular cuántos bloques hay considerando el offset
            start_x = offset_x if offset_x >= 0 else offset_x % cell_size
            start_y = offset_y if offset_y >= 0 else offset_y % cell_size
            
            for y in range(start_y, height, cell_size):
                for x in range(start_x, width, cell_size):
                    cx = x + cell_size // 2
                    cy = y + cell_size // 2
                    if 0 <= cx < width and 0 <= cy < height:
                        pixel_color = image.getpixel((cx, cy))[:3]
                        
                        is_excluded = any(
                            self.colors_similar(pixel_color, exc, tolerance=10)
                            for exc in excluded
                        )
                        
                        if is_excluded:
                            center_color = (255, 100, 100, 200)
                            draw.line([(cx - marker_size, cy - marker_size),
                                      (cx + marker_size, cy + marker_size)], 
                                     fill=center_color, width=2)
                            draw.line([(cx + marker_size, cy - marker_size),
                                      (cx - marker_size, cy + marker_size)], 
                                     fill=center_color, width=2)
                        else:
                            center_color = (50, 255, 100, 200)
                            draw.ellipse(
                                [(cx - marker_size, cy - marker_size),
                                 (cx + marker_size, cy + marker_size)],
                                fill=center_color
                            )
        
        return Image.alpha_composite(viz_image, overlay)
        
    def colors_similar(self, c1, c2, tolerance=10):
        """Compara si dos colores son similares."""
        return all(abs(a - b) <= tolerance for a, b in zip(c1, c2))
        
    def transform_image(self):
        """Transforma la imagen a pixel art real."""
        if self.original_image is None:
            return
            
        cell_size = self.get_current_grid_size()
        if cell_size < 2:
            messagebox.showwarning("Aviso", "El tamaño de grid debe ser al menos 2")
            return
            
        width, height = self.original_image.size
        offset_x = self.grid_offset_x.get()
        offset_y = self.grid_offset_y.get()
        
        # Calcular dimensiones considerando offset
        start_x = offset_x if offset_x >= 0 else offset_x % cell_size
        start_y = offset_y if offset_y >= 0 else offset_y % cell_size
        
        new_w = (width - start_x) // cell_size
        new_h = (height - start_y) // cell_size
        
        if new_w < 1 or new_h < 1:
            messagebox.showwarning("Aviso", "El offset es demasiado grande para el tamaño de imagen")
            return
        
        excluded = self.color_exclusion.get_excluded_colors()
        
        self.result_image = Image.new('RGBA', (new_w, new_h), (0, 0, 0, 0))
        
        excluded_count = 0
        
        for y in range(new_h):
            for x in range(new_w):
                orig_x = start_x + x * cell_size
                orig_y = start_y + y * cell_size
                
                cx = orig_x + cell_size // 2
                cy = orig_y + cell_size // 2
                cx = min(cx, width - 1)
                cy = min(cy, height - 1)
                
                color = self.original_image.getpixel((cx, cy))
                if len(color) == 3:
                    color = color + (255,)
                
                rgb = color[:3]
                
                is_excluded = any(
                    self.colors_similar(rgb, exc, tolerance=10)
                    for exc in excluded
                )
                
                if is_excluded:
                    self.result_image.putpixel((x, y), (0, 0, 0, 0))
                    excluded_count += 1
                else:
                    self.result_image.putpixel((x, y), color)
        
        self.grid_image = self.create_grid_visualization(
            self.original_image, cell_size, True, offset_x, offset_y
        )
        
        self.result_canvas.set_image(self.result_image)
        self.compare_left.set_image(self.original_image)
        self.compare_right.set_image(self.result_image)
        
        total_pixels = new_w * new_h
        excluded_text = f"\nPixels excluidos: {excluded_count}" if excluded_count > 0 else ""
        offset_text = f"\nOffset: ({offset_x}, {offset_y})" if (offset_x != 0 or offset_y != 0) else ""
        
        self.result_info.config(
            text=f"✅ Transformación completada\n"
                 f"Original: {width}×{height}\n"
                 f"Resultado: {new_w}×{new_h}\n"
                 f"Factor: {cell_size}×{offset_text}{excluded_text}"
        )
        
        self.save_btn.state(['!disabled'])
        self.save_grid_btn.state(['!disabled'])
        self.notebook.select(1)
        
    def save_result(self):
        """Guarda la imagen resultado."""
        if self.result_image is None:
            return
            
        default_name = f"{self.original_path.stem}_real.png" if self.original_path else "result.png"
        
        filepath = filedialog.asksaveasfilename(
            title="Guardar imagen resultado",
            defaultextension=".png",
            initialfile=default_name,
            filetypes=[("PNG", "*.png"), ("Todos", "*.*")]
        )
        
        if filepath:
            self.result_image.save(filepath, 'PNG')
            messagebox.showinfo("Guardado", f"Imagen guardada:\n{filepath}")
            
    def save_grid(self):
        """Guarda la visualización del grid."""
        if self.grid_image is None:
            return
            
        default_name = f"{self.original_path.stem}_grid.png" if self.original_path else "grid.png"
        
        filepath = filedialog.asksaveasfilename(
            title="Guardar visualización del grid",
            defaultextension=".png",
            initialfile=default_name,
            filetypes=[("PNG", "*.png"), ("Todos", "*.*")]
        )
        
        if filepath:
            self.grid_image.save(filepath, 'PNG')
            messagebox.showinfo("Guardado", f"Grid guardado:\n{filepath}")


def main():
    root = tk.Tk()
    app = PixelArtTransformerGUI(root)
    
    root.update_idletasks()
    w = root.winfo_width()
    h = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (w // 2)
    y = (root.winfo_screenheight() // 2) - (h // 2)
    root.geometry(f'+{x}+{y}')
    
    root.mainloop()


if __name__ == '__main__':
    main()
