"""
Pixel Art Transformer - Interfaz Gráfica
=========================================
Aplicación con GUI para convertir imágenes de pixel art escaladas
a su forma real (1 pixel por pixel).
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import numpy as np
from pathlib import Path
import threading


class PixelArtTransformerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎨 Pixel Art Transformer")
        self.root.geometry("1200x800")
        self.root.minsize(900, 600)
        
        # Variables
        self.original_image = None
        self.original_path = None
        self.result_image = None
        self.grid_image = None
        self.detected_size = tk.IntVar(value=0)
        self.manual_size = tk.IntVar(value=16)
        self.use_auto_detect = tk.BooleanVar(value=True)
        self.show_grid_overlay = tk.BooleanVar(value=True)
        self.show_center_markers = tk.BooleanVar(value=True)
        
        # Estilo
        self.setup_style()
        
        # Layout principal
        self.create_widgets()
        
    def setup_style(self):
        """Configura el estilo visual de la aplicación."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Colores
        bg_color = '#1a1a2e'
        fg_color = '#eaeaea'
        accent_color = '#e94560'
        secondary_color = '#16213e'
        
        self.root.configure(bg=bg_color)
        
        style.configure('TFrame', background=bg_color)
        style.configure('TLabel', background=bg_color, foreground=fg_color, font=('Segoe UI', 10))
        style.configure('Title.TLabel', font=('Segoe UI', 14, 'bold'), foreground=accent_color)
        style.configure('Info.TLabel', font=('Segoe UI', 9), foreground='#888888')
        style.configure('TButton', font=('Segoe UI', 10), padding=10)
        style.configure('Accent.TButton', font=('Segoe UI', 11, 'bold'))
        style.configure('TCheckbutton', background=bg_color, foreground=fg_color)
        style.configure('TRadiobutton', background=bg_color, foreground=fg_color)
        style.configure('TScale', background=bg_color)
        style.configure('TLabelframe', background=bg_color, foreground=fg_color)
        style.configure('TLabelframe.Label', background=bg_color, foreground=accent_color, font=('Segoe UI', 10, 'bold'))
        
    def create_widgets(self):
        """Crea todos los widgets de la interfaz."""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Panel izquierdo (controles)
        left_panel = ttk.Frame(main_frame, width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # Panel derecho (vista previa)
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.create_control_panel(left_panel)
        self.create_preview_panel(right_panel)
        
    def create_control_panel(self, parent):
        """Crea el panel de controles."""
        # Título
        title = ttk.Label(parent, text="🎨 Pixel Art Transformer", style='Title.TLabel')
        title.pack(pady=(0, 20))
        
        # --- Sección: Cargar imagen ---
        load_frame = ttk.LabelFrame(parent, text="📂 Imagen", padding=10)
        load_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.load_btn = ttk.Button(load_frame, text="Cargar Imagen", command=self.load_image)
        self.load_btn.pack(fill=tk.X)
        
        self.file_label = ttk.Label(load_frame, text="Ningún archivo seleccionado", style='Info.TLabel', wraplength=250)
        self.file_label.pack(pady=(5, 0))
        
        self.size_label = ttk.Label(load_frame, text="", style='Info.TLabel')
        self.size_label.pack()
        
        # --- Sección: Configuración del Grid ---
        grid_frame = ttk.LabelFrame(parent, text="📐 Tamaño del Grid", padding=10)
        grid_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Auto-detectar
        auto_radio = ttk.Radiobutton(
            grid_frame, text="Auto-detectar", 
            variable=self.use_auto_detect, value=True,
            command=self.on_grid_mode_change
        )
        auto_radio.pack(anchor=tk.W)
        
        self.auto_result_label = ttk.Label(grid_frame, text="", style='Info.TLabel')
        self.auto_result_label.pack(anchor=tk.W, padx=(20, 0))
        
        # Manual
        manual_radio = ttk.Radiobutton(
            grid_frame, text="Manual:", 
            variable=self.use_auto_detect, value=False,
            command=self.on_grid_mode_change
        )
        manual_radio.pack(anchor=tk.W, pady=(10, 0))
        
        # Slider para tamaño manual
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
        
        # --- Sección: Opciones de visualización ---
        viz_frame = ttk.LabelFrame(parent, text="👁️ Visualización", padding=10)
        viz_frame.pack(fill=tk.X, pady=(0, 15))
        
        grid_check = ttk.Checkbutton(
            viz_frame, text="Mostrar grid en preview",
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
        
        # --- Sección: Acciones ---
        action_frame = ttk.LabelFrame(parent, text="⚡ Acciones", padding=10)
        action_frame.pack(fill=tk.X, pady=(0, 15))
        
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
        self.result_frame = ttk.LabelFrame(parent, text="📊 Resultado", padding=10)
        self.result_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.result_info = ttk.Label(self.result_frame, text="Transforma una imagen para ver los resultados", style='Info.TLabel', wraplength=250)
        self.result_info.pack()
        
    def create_preview_panel(self, parent):
        """Crea el panel de vista previa."""
        # Notebook para las pestañas
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Pestaña 1: Original con Grid
        self.original_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.original_tab, text="📷 Original + Grid")
        
        self.original_canvas = tk.Canvas(self.original_tab, bg='#0f0f23', highlightthickness=0)
        self.original_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Pestaña 2: Resultado
        self.result_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.result_tab, text="✨ Resultado")
        
        self.result_canvas = tk.Canvas(self.result_tab, bg='#0f0f23', highlightthickness=0)
        self.result_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Pestaña 3: Comparación
        self.compare_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.compare_tab, text="🔄 Comparar")
        
        compare_frame = ttk.Frame(self.compare_tab)
        compare_frame.pack(fill=tk.BOTH, expand=True)
        
        self.compare_left = tk.Canvas(compare_frame, bg='#0f0f23', highlightthickness=0)
        self.compare_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.compare_right = tk.Canvas(compare_frame, bg='#0f0f23', highlightthickness=0)
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
                
                # Actualizar labels
                self.file_label.config(text=self.original_path.name)
                self.size_label.config(text=f"Dimensiones: {self.original_image.size[0]}×{self.original_image.size[1]}")
                
                # Auto-detectar tamaño
                self.detect_grid_size()
                
                # Habilitar botones
                self.transform_btn.state(['!disabled'])
                
                # Mostrar preview
                self.update_preview()
                
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cargar la imagen:\n{e}")
                
    def detect_grid_size(self):
        """Detecta automáticamente el tamaño del grid."""
        if self.original_image is None:
            return
            
        img_array = np.array(self.original_image.convert('RGB'))
        width, height = self.original_image.size
        
        # Tamaños comunes en pixel art
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
            
    def get_current_grid_size(self):
        """Obtiene el tamaño de grid actual."""
        if self.use_auto_detect.get():
            return self.detected_size.get()
        return self.manual_size.get()
        
    def update_preview(self):
        """Actualiza la vista previa."""
        if self.original_image is None:
            return
            
        cell_size = self.get_current_grid_size()
        if cell_size < 2:
            return
            
        # Crear imagen con grid overlay
        if self.show_grid_overlay.get():
            preview_img = self.create_grid_visualization(
                self.original_image, cell_size,
                self.show_center_markers.get()
            )
        else:
            preview_img = self.original_image.copy()
            if preview_img.mode != 'RGBA':
                preview_img = preview_img.convert('RGBA')
        
        # Mostrar en canvas
        self.display_image_on_canvas(preview_img, self.original_canvas)
        
    def create_grid_visualization(self, image, cell_size, show_centers=True):
        """Crea visualización del grid."""
        if image.mode != 'RGBA':
            viz_image = image.convert('RGBA')
        else:
            viz_image = image.copy()
        
        overlay = Image.new('RGBA', viz_image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        width, height = image.size
        grid_color = (255, 50, 80, 150)
        
        # Líneas verticales
        for x in range(0, width + 1, cell_size):
            draw.line([(x, 0), (x, height)], fill=grid_color, width=1)
        
        # Líneas horizontales
        for y in range(0, height + 1, cell_size):
            draw.line([(0, y), (width, y)], fill=grid_color, width=1)
        
        # Centros
        if show_centers:
            center_color = (50, 255, 100, 200)
            marker_size = max(1, cell_size // 8)
            
            for y in range(0, height, cell_size):
                for x in range(0, width, cell_size):
                    cx = x + cell_size // 2
                    cy = y + cell_size // 2
                    if cx < width and cy < height:
                        draw.ellipse(
                            [(cx - marker_size, cy - marker_size),
                             (cx + marker_size, cy + marker_size)],
                            fill=center_color
                        )
        
        return Image.alpha_composite(viz_image, overlay)
        
    def display_image_on_canvas(self, image, canvas):
        """Muestra una imagen en un canvas, escalada para ajustar."""
        canvas.update()
        canvas_w = canvas.winfo_width()
        canvas_h = canvas.winfo_height()
        
        if canvas_w < 10 or canvas_h < 10:
            return
            
        img_w, img_h = image.size
        
        # Calcular escala para ajustar
        scale = min(canvas_w / img_w, canvas_h / img_h, 4.0)  # Max 4x zoom
        
        new_w = max(1, int(img_w * scale))
        new_h = max(1, int(img_h * scale))
        
        # Usar NEAREST para pixel art
        resized = image.resize((new_w, new_h), Image.Resampling.NEAREST)
        
        # Convertir a PhotoImage
        photo = ImageTk.PhotoImage(resized)
        
        # Guardar referencia
        canvas.photo = photo
        
        # Centrar en canvas
        x = (canvas_w - new_w) // 2
        y = (canvas_h - new_h) // 2
        
        canvas.delete("all")
        canvas.create_image(x, y, anchor=tk.NW, image=photo)
        
    def transform_image(self):
        """Transforma la imagen a pixel art real."""
        if self.original_image is None:
            return
            
        cell_size = self.get_current_grid_size()
        if cell_size < 2:
            messagebox.showwarning("Aviso", "El tamaño de grid debe ser al menos 2")
            return
            
        width, height = self.original_image.size
        new_w = width // cell_size
        new_h = height // cell_size
        
        # Convertir si es paleta
        img = self.original_image
        if img.mode == 'P':
            img = img.convert('RGBA')
        
        # Crear nueva imagen
        self.result_image = Image.new(img.mode, (new_w, new_h))
        
        for y in range(new_h):
            for x in range(new_w):
                orig_x = x * cell_size
                orig_y = y * cell_size
                
                # Centro de la celda
                cx = orig_x + cell_size // 2
                cy = orig_y + cell_size // 2
                cx = min(cx, width - 1)
                cy = min(cy, height - 1)
                
                color = img.getpixel((cx, cy))
                self.result_image.putpixel((x, y), color)
        
        # Guardar imagen del grid
        self.grid_image = self.create_grid_visualization(
            self.original_image, cell_size, True
        )
        
        # Mostrar resultado
        self.display_image_on_canvas(self.result_image, self.result_canvas)
        
        # Mostrar comparación
        self.display_image_on_canvas(self.original_image, self.compare_left)
        self.display_image_on_canvas(self.result_image, self.compare_right)
        
        # Actualizar info
        self.result_info.config(
            text=f"✅ Transformación completada\n"
                 f"Original: {width}×{height}\n"
                 f"Resultado: {new_w}×{new_h}\n"
                 f"Factor: {cell_size}×"
        )
        
        # Habilitar guardar
        self.save_btn.state(['!disabled'])
        self.save_grid_btn.state(['!disabled'])
        
        # Cambiar a pestaña de resultado
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
    
    # Centrar ventana
    root.update_idletasks()
    w = root.winfo_width()
    h = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (w // 2)
    y = (root.winfo_screenheight() // 2) - (h // 2)
    root.geometry(f'+{x}+{y}')
    
    root.mainloop()


if __name__ == '__main__':
    main()
