#!/bin/bash

echo "🎨 Pixel Art Transformer - Instalador"
echo "======================================"
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 no encontrado. Instálalo con:"
    echo "   sudo apt install python3 python3-pip python3-tk"
    exit 1
fi

echo "✅ Python3 encontrado: $(python3 --version)"

# Verificar tkinter
python3 -c "import tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  tkinter no encontrado. Instalando..."
    echo "   Ejecuta: sudo apt install python3-tk"
    exit 1
fi

echo "✅ tkinter disponible"

# Instalar dependencias
echo ""
echo "📦 Instalando dependencias..."
pip3 install --user -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ ¡Instalación completada!"
    echo ""
    echo "🚀 Para ejecutar:"
    echo "   python3 pixel_art_gui.py"
    echo ""
    
    read -p "¿Ejecutar ahora? (s/n): " choice
    if [ "$choice" = "s" ] || [ "$choice" = "S" ]; then
        python3 pixel_art_gui.py
    fi
else
    echo "❌ Error instalando dependencias"
    exit 1
fi
