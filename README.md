# 🎨 Pixel Art Transformer (Full AI)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-green" alt="Platform">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
</p>

Convert scaled pixel art images to their **true pixel dimensions** (1 pixel = 1 pixel).

Takes any upscaled pixel art image, detects the original pixel grid, samples the center color of each cell, and outputs a clean PNG at the real resolution.

## ✨ Features

- 🔍 **Auto-detection** of pixel size
- 📐 **Grid visualization** overlay
- 🎯 **Center sampling** for accurate colors
- 💾 **Lossless PNG** export
- 🖥️ **GUI** and **CLI** interfaces

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/PythonPixelArtTransformer.git
cd PythonPixelArtTransformer

# Install dependencies
pip install -r requirements.txt
```

### Linux One-Liner
```bash
chmod +x install.sh && ./install.sh
```

## 🎮 Usage

### GUI (Recommended)
```bash
python pixel_art_gui.py
```

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
```

## 📋 Requirements

- Python 3.8+
- Pillow
- NumPy
- tkinter (included with Python)

## 🖼️ Example

| Input (128×128) | Grid Visualization | Output (8×8) |
|:---:|:---:|:---:|
| Scaled 16× | Shows sampling points | True pixels |

## 📄 License

MIT License - feel free to use in your projects!
