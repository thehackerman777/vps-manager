#!/usr/bin/env bash
# VPS Manager — Linux / macOS launcher
set -euo pipefail
cd "$(dirname "$0")"

echo "==> Installing / verifying dependencies..."
pip install -q -r requirements.txt

echo "==> Starting VPS Manager..."
exec python main.py
