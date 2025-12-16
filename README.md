# 🎨 Pixel Art Transformer

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-green" alt="Platform">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
  <img src="https://img.shields.io/badge/Tests-Passing-brightgreen" alt="Tests">
</p>

Convert upscaled pixel art images to their **true pixel dimensions** (1 pixel = 1 pixel).

Takes any upscaled pixel art image, automatically detects the original pixel grid, samples the center color of each cell, and outputs a clean PNG at the real resolution.

## ✨ Features

- 🔍 **Auto-detection** of pixel size using pattern analysis
- 📐 **Grid visualization** overlay with center markers
- 🎯 **Center sampling** for accurate color preservation
- 🚫 **Color exclusion** with tolerance control
- 🎨 **Bit depth reduction** for retro palette effects
- 💾 **Lossless PNG** export
- 🖥️ **GUI** and **CLI** interfaces
- 🧪 **Comprehensive test suite**

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/Zero-AI-Hub/PythonPixelArtTransformer.git
cd PythonPixelArtTransformer

# Install dependencies
pip install -r requirements.txt
```

### Windows
```batch
install.bat
```

### Linux/macOS
```bash
chmod +x install.sh && ./install.sh
```

## 🎮 Usage

### GUI (Recommended)

```bash
python pixel_art_gui.py
```

The GUI provides a wizard-style workflow:
1. **Load** - Select your upscaled pixel art image
2. **Select** - Draw rectangles around sprites/regions
3. **Configure** - Adjust grid size, colors, and exclusions
4. **Generate** - Export transformed images

### Command Line

```bash
# Auto-detect pixel size
python pixel_art_transformer.py image.png

# Show grid visualization
python pixel_art_transformer.py image.png --show-grid

# Manual pixel size
python pixel_art_transformer.py image.png --grid-size 16

# Custom output name
python pixel_art_transformer.py image.png -o output.png

# Verbose mode
python pixel_art_transformer.py image.png -v
```

### Python API

```python
from core import detect_pixel_size, transform_to_real_pixels
from PIL import Image

# Load image
image = Image.open("sprite_sheet.png")

# Auto-detect grid size
cell_size = detect_pixel_size(image)
print(f"Detected: {cell_size}x{cell_size}")

# Transform to true pixels
result = transform_to_real_pixels(
    image, 
    cell_size,
    bit_depth=8,
    excluded_colors=[(255, 0, 255)],  # Exclude magenta
    tolerance=10
)

result.save("sprite_sheet_real.png")
```

## 📁 Project Structure

```
PythonPixelArtTransformer/
├── pixel_art_gui.py          # Main GUI application
├── pixel_art_transformer.py  # CLI application
├── config.py                 # Centralized configuration
├── core/                     # Core processing logic
│   ├── __init__.py
│   ├── transformer.py        # Image processing functions
│   └── exceptions.py         # Custom exceptions
├── gui/                      # GUI components
│   ├── __init__.py
│   ├── canvases.py          # Zoomable canvas widgets
│   └── steps.py             # Wizard step frames
├── tests/                    # Test suite
│   ├── __init__.py
│   ├── test_transformer.py
│   └── test_config.py
├── examples/                 # Example files
│   └── create_test_image.py
├── requirements.txt          # Production dependencies
├── requirements-dev.txt      # Development dependencies
├── install.sh               # Linux/macOS installer
├── install.bat              # Windows installer
├── run.sh                   # Linux/macOS runner
└── run.bat                  # Windows runner
```

## 🧪 Testing

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ -v --cov=core --cov-report=html

# Type checking
python -m mypy core/ --ignore-missing-imports
```

## 📋 Requirements

- **Python 3.10+**
- **Pillow** >= 9.0.0
- **NumPy** >= 1.21.0
- **tkinter** (included with Python)

## 🔧 Configuration

All settings are centralized in `config.py`:

| Setting | Description |
|---------|-------------|
| `UI_COLORS` | Application color scheme |
| `ZOOM` | Canvas zoom limits and factors |
| `GRID_DETECTION` | Auto-detection thresholds |
| `REGION` | Region selection parameters |
| `COLOR` | Bit depth options |
| `WINDOW` | Window dimensions |
| `FILE` | Supported formats and suffixes |

## 🖼️ Example

```
Input (128×128)     →     Output (8×8)
┌────────────────┐       ┌────────┐
│ Upscaled 16×   │ ───▶  │ True   │
│ pixel art      │       │ pixels │
└────────────────┘       └────────┘
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Write tests for your changes
4. Ensure all tests pass: `python -m pytest tests/ -v`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 📝 Changelog

### v6.0.0 (2024-12)
- Complete codebase refactoring
- Modular architecture with `core/` and `gui/` packages
- Centralized configuration in `config.py`
- Custom exceptions for better error handling
- Comprehensive test suite
- Type hints throughout
- Windows batch scripts
- Improved documentation

### v5.0.0
- Initial public release
- GUI with wizard workflow
- CLI with auto-detection
- Grid visualization

## 📄 License

MIT License - feel free to use in your projects!

---

<p align="center">
  Made with ❤️ for pixel art enthusiasts
</p>
