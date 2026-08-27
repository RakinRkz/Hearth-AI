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

# Build the frontend - build.spec bundles frontend/dist, so it must exist first
echo "🎨 Building frontend..."
if ! command -v npm > /dev/null; then
    echo "❌ npm not found. Node.js 18+ is required to build the frontend."
    exit 1
fi
(cd frontend && npm install --silent && npm run build)

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
1. Run HearthAI (or HearthAI.exe on Windows)
2. Open http://127.0.0.1:8080 in your browser
3. On first run, Hearth AI offers to download a starter model for you

Prefer your own model? Drop a .gguf file into the "models" folder before
starting, then pick it in Settings.

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
