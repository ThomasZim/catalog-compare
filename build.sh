#!/bin/bash
# Build macOS .app

set -e

echo "Creating venv..."
python3 -m venv .venv
source .venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt pyinstaller

echo "Building application..."
pyinstaller --onefile --windowed \
    --name "Catalog Compare" \
    --collect-all fpdf2 \
    run.py

echo "Build complete! Application in dist/"
