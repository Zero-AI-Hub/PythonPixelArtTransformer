"""
Pixel Art Transformer - Graphical User Interface v6
====================================================
Wizard-style interface for converting upscaled pixel art to true pixel dimensions.

Workflow:
1. Load image
2. Select regions (rectangles) containing sprites
3. Configure each region (grid size, colors, exclusions)
4. Generate and save transformed regions

Optimized for 1920x1080
"""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL.Image import Image as PILImage

from config import UI_COLORS, WINDOW, setup_logging
from core import transform_to_real_pixels
from core.exceptions import PixelArtError, ProcessingError
from gui import Step1Frame, Step2Frame, Step3Frame, Step4Frame


# Module logger
logger = setup_logging()


class PixelArtTransformerGUI:
    """
    Main application class for the Pixel Art Transformer GUI.
    
    Manages the wizard-style workflow through four steps:
    1. Image loading
    2. Region selection
    3. Region configuration
    4. Result generation and saving
    
    Attributes:
        root: The Tkinter root window.
        original_image: The loaded source image.
        original_path: Path to the source image file.
        regions: List of region configurations.
        results: Dictionary mapping region index to result image.
    """
    
    def __init__(self, root: tk.Tk):
        """
        Initialize the application.
        
        Args:
            root: Tkinter root window.
        """
        self.root = root
        self.root.title(WINDOW.title)
        self.root.geometry(WINDOW.default_geometry)
        self.root.minsize(WINDOW.min_width, WINDOW.min_height)
        
        self.original_image: PILImage | None = None
        self.original_path: Path | None = None
        self.regions: list[dict] = []
        self.results: dict[int, PILImage] = {}
        
        self._setup_style()
        self._create_widgets()
        self._show_step(1)
        
        logger.info("GUI initialized")
    
    def _setup_style(self) -> None:
        """Configure ttk styles for the application."""
        style = ttk.Style()
        style.theme_use('clam')
        
        self.root.configure(bg=UI_COLORS.background)
        
        # Frame styles
        style.configure('TFrame', background=UI_COLORS.background)
        
        # Label styles
        style.configure(
            'TLabel', 
            background=UI_COLORS.background, 
            foreground=UI_COLORS.foreground, 
            font=('Segoe UI', 10)
        )
        style.configure(
            'Title.TLabel', 
            font=('Segoe UI', 12, 'bold'), 
            foreground=UI_COLORS.accent
        )
        style.configure(
            'Step.TLabel', 
            font=('Segoe UI', 11, 'bold'), 
            foreground=UI_COLORS.accent_green
        )
        style.configure(
            'Info.TLabel', 
            font=('Segoe UI', 9), 
            foreground=UI_COLORS.muted
        )
        
        # Button styles
        style.configure('TButton', font=('Segoe UI', 10), padding=5)
        style.configure('Accent.TButton', font=('Segoe UI', 10, 'bold'))
        
        # Checkbutton and radiobutton
        style.configure(
            'TCheckbutton', 
            background=UI_COLORS.background, 
            foreground=UI_COLORS.foreground
        )
        style.configure(
            'TRadiobutton', 
            background=UI_COLORS.background, 
            foreground=UI_COLORS.foreground
        )
        
        # Labelframe
        style.configure(
            'TLabelframe', 
            background=UI_COLORS.background, 
            foreground=UI_COLORS.foreground
        )
        style.configure(
            'TLabelframe.Label', 
            background=UI_COLORS.background, 
            foreground=UI_COLORS.accent, 
            font=('Segoe UI', 9, 'bold')
        )
    
    def _create_widgets(self) -> None:
        """Create all application widgets."""
        # Header
        header = ttk.Frame(self.root)
        header.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(
            header, 
            text="🎨 Pixel Art Transformer", 
            style='Title.TLabel'
        ).pack(side=tk.LEFT)
        
        self.step_label = ttk.Label(
            header, 
            text="Paso 1: Cargar imagen", 
            style='Step.TLabel'
        )
        self.step_label.pack(side=tk.RIGHT)
        
        # Main container
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create step frames
        self.step1_frame = Step1Frame(
            self.main_container,
            on_image_loaded=self._on_image_loaded
        )
        
        self.step2_frame = Step2Frame(
            self.main_container,
            on_back=lambda: self._show_step(1),
            on_continue=self._on_regions_selected
        )
        
        self.step3_frame = Step3Frame(
            self.main_container,
            on_back=lambda: self._show_step(2),
            on_generate=self._generate_all
        )
        
        self.step4_frame = Step4Frame(
            self.main_container,
            on_back=lambda: self._show_step(3),
            on_new=lambda: self._show_step(1)
        )
    
    def _show_step(self, step: int) -> None:
        """
        Show the specified step.
        
        Args:
            step: Step number (1-4).
        """
        # Hide all frames
        for frame in [
            self.step1_frame, 
            self.step2_frame, 
            self.step3_frame, 
            self.step4_frame
        ]:
            frame.pack_forget()
        
        # Show requested step
        steps = {
            1: (self.step1_frame, "Paso 1: Cargar imagen"),
            2: (self.step2_frame, "Paso 2: Seleccionar regiones"),
            3: (self.step3_frame, "Paso 3: Configurar regiones"),
            4: (self.step4_frame, "Paso 4: Resultado"),
        }
        
        frame, label = steps[step]
        frame.pack(fill=tk.BOTH, expand=True)
        self.step_label.config(text=label)
        
        logger.debug("Showing step %d", step)
    
    def _on_image_loaded(self, image: PILImage, path: Path) -> None:
        """
        Handle image loaded event.
        
        Args:
            image: Loaded PIL Image.
            path: Path to the image file.
        """
        self.original_image = image
        self.original_path = path
        self.regions = []
        self.results = {}
        
        logger.info("Loaded image: %s (%dx%d)", path.name, *image.size)
        
        # Setup step 2
        self.step2_frame.set_image(image)
        self._show_step(2)
    
    def _on_regions_selected(self, regions: list[dict]) -> None:
        """
        Handle regions selected event.
        
        Args:
            regions: List of region configurations.
        """
        self.regions = regions
        
        logger.info("Selected %d regions", len(regions))
        
        # Setup step 3
        self.step3_frame.set_data(self.original_image, regions)
        self._show_step(3)
    
    def _generate_all(self, regions: list[dict]) -> None:
        """
        Generate transformed images for all regions.
        
        Args:
            regions: List of region configurations.
        """
        self.regions = regions
        self.results = {}
        
        logger.info("Generating %d regions", len(regions))
        
        for idx, region in enumerate(regions):
            try:
                result = self._process_region(region)
                if result is not None:
                    self.results[idx] = result
                    logger.debug("Generated region %d: %dx%d", idx, *result.size)
            except PixelArtError as e:
                logger.error("Failed to process region %d: %s", idx, e)
                messagebox.showwarning(
                    "Advertencia", 
                    f"No se pudo procesar la región {idx + 1}:\n{e}"
                )
            except Exception as e:
                logger.exception("Unexpected error processing region %d", idx)
                messagebox.showerror(
                    "Error", 
                    f"Error inesperado en región {idx + 1}:\n{e}"
                )
        
        if self.results:
            self.step4_frame.set_results(self.results, self.original_path)
            self._show_step(4)
        else:
            messagebox.showerror(
                "Error", 
                "No se pudo generar ninguna región."
            )
    
    def _process_region(self, region: dict) -> PILImage | None:
        """
        Process a single region.
        
        Args:
            region: Region configuration dictionary.
        
        Returns:
            Transformed PIL Image, or None if processing failed.
        
        Raises:
            ProcessingError: If processing fails.
        """
        from core import transform_with_custom_grid
        
        if self.original_image is None:
            raise ProcessingError("process_region", "No image loaded")
        
        x1, y1, x2, y2 = region['coords']
        
        # Extract region
        region_image = self.original_image.crop((x1, y1, x2, y2))
        
        # Check if we have a custom grid config
        grid_config = region.get('grid_config')
        
        try:
            if grid_config and hasattr(grid_config, 'x_lines'):
                # Use custom grid transformation
                result = transform_with_custom_grid(
                    image=region_image,
                    x_lines=grid_config.x_lines,
                    y_lines=grid_config.y_lines,
                    excluded_cells=grid_config.excluded_cells,
                    bit_depth=region.get('bits', 8),
                    excluded_colors=region.get('excluded_colors'),
                    tolerance=region.get('tolerance', 10)
                )
            else:
                # Use uniform grid transformation
                result = transform_to_real_pixels(
                    image=region_image,
                    cell_size=region['grid_size'],
                    offset_x=region.get('offset_x', 0),
                    offset_y=region.get('offset_y', 0),
                    bit_depth=region.get('bits', 8),
                    excluded_colors=region.get('excluded_colors'),
                    tolerance=region.get('tolerance', 10)
                )
            return result
        except ValueError as e:
            raise ProcessingError("transform", str(e))


def main() -> None:
    """Main entry point for the GUI application."""
    from PIL import Image, ImageTk
    import os
    
    # Get the directory where the script is located
    script_dir = Path(__file__).parent
    icon_path = script_dir / "assets" / "icon.png"
    
    # Create splash screen
    splash = tk.Tk()
    splash.title("")
    splash.overrideredirect(True)  # Remove window decorations
    splash.configure(bg='#1a1a2e')
    
    # Center splash screen
    splash_width, splash_height = 300, 350
    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    x = (screen_width - splash_width) // 2
    y = (screen_height - splash_height) // 2
    splash.geometry(f'{splash_width}x{splash_height}+{x}+{y}')
    
    # Load and display icon on splash
    splash_icon = None
    if icon_path.exists():
        try:
            img = Image.open(icon_path)
            # Resize for splash screen
            img = img.resize((150, 150), Image.Resampling.NEAREST)
            splash_icon = ImageTk.PhotoImage(img)
        except Exception:
            pass
    
    # Splash content
    if splash_icon:
        icon_label = tk.Label(splash, image=splash_icon, bg='#1a1a2e')
        icon_label.pack(pady=30)
    
    title_label = tk.Label(
        splash, 
        text="🎨 Pixel Art Transformer",
        font=('Segoe UI', 16, 'bold'),
        fg='#e94560',
        bg='#1a1a2e'
    )
    title_label.pack(pady=10)
    
    version_label = tk.Label(
        splash,
        text="v6.0",
        font=('Segoe UI', 10),
        fg='#888888',
        bg='#1a1a2e'
    )
    version_label.pack()
    
    loading_label = tk.Label(
        splash,
        text="Cargando...",
        font=('Segoe UI', 9),
        fg='#00ff88',
        bg='#1a1a2e'
    )
    loading_label.pack(pady=20)
    
    splash.update()
    
    # Close splash and create main window after delay
    def start_main_app():
        splash.destroy()
        
        root = tk.Tk()
        
        # Set app icon
        if icon_path.exists():
            try:
                icon_img = Image.open(icon_path)
                icon_photo = ImageTk.PhotoImage(icon_img)
                root.iconphoto(True, icon_photo)
            except Exception:
                pass
        
        try:
            app = PixelArtTransformerGUI(root)
            
            # Center window
            root.update_idletasks()
            x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
            y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
            root.geometry(f'+{x}+{y}')
            
            root.mainloop()
            
        except Exception as e:
            logger.exception("Fatal error")
            messagebox.showerror("Error Fatal", f"La aplicación encontró un error:\n{e}")
            raise
    
    # Show splash for 1.5 seconds then start main app
    splash.after(1500, start_main_app)
    splash.mainloop()


if __name__ == '__main__':
    main()
