#!/bin/bash
# Build script for Hearth AI
# Usage: ./build.sh [windows|linux|macos]

set -e

APP_NAME="HearthAI"
VERSION="1.0.0"

echo "🔨 Building $APP_NAME v$VERSION"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ Virtual environment not found. Run: python -m venv venv"
    exit 1
fi

# Install PyInstaller if not present
pip install pyinstaller --quiet

# Clean previous builds
rm -rf build/ dist/

# Build
echo "📦 Running PyInstaller..."
pyinstaller build.spec --noconfirm

# Create distribution package
echo "📁 Creating distribution package..."

DIST_DIR="dist/$APP_NAME"

# Create necessary directories in dist
mkdir -p "$DIST_DIR/models"
mkdir -p "$DIST_DIR/data/conversations"
mkdir -p "$DIST_DIR/data/vectorstore"
mkdir -p "$DIST_DIR/documents"

# Copy README
cat > "$DIST_DIR/README.txt" << 'EOF'
Hearth AI - Local AI Chat Application
=====================================

Quick Start:
1. Download a GGUF model from HuggingFace
   (e.g., Llama 3.2 3B, Mistral 7B, Phi-3 Mini)
2. Place the .gguf file in the "models" folder
3. Run HearthAI (or HearthAI.exe on Windows)
4. Go to Settings → Browse → Select your model → Load

Features:
- 💬 Chat with local AI
- 📄 RAG: Upload documents and ask questions
- 🌐 Web Search: Get answers from the internet

Model Recommendations:
- Llama 3.2 3B Q4_K_M (~2GB) - Good balance
- Mistral 7B Q4_K_M (~4GB) - Better quality
- Phi-3 Mini Q4_K_M (~2.4GB) - Fast and small

Download models from:
https://huggingface.co/models?search=gguf

For GPU acceleration, download the GPU version from releases.

Need help? Visit: https://github.com/RakinRkz/Hearth-AI
EOF

echo "✅ Build complete!"
echo "📂 Output: dist/$APP_NAME/"
echo ""
echo "To distribute:"
echo "  Linux:   tar -czvf ${APP_NAME}-${VERSION}-linux.tar.gz -C dist $APP_NAME"
echo "  Windows: (zip the dist/$APP_NAME folder)"
echo "  macOS:   (create DMG or zip the .app bundle)"
