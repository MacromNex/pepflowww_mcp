#!/bin/bash
# Quick Setup Script for PepFlowww MCP
# PepFlow: Full-Atom Peptide Design based on Multi-modal Flow Matching (ICML 2024)
# Generates peptide structures for protein binding pockets
# Source: https://github.com/Ced3-han/PepFlowww

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Setting up PepFlowww MCP ==="

# Step 1: Create Python environment
echo "[1/7] Creating Python 3.10 environment..."
(command -v mamba >/dev/null 2>&1 && mamba create -p ./env python=3.10 -y) || \
(command -v conda >/dev/null 2>&1 && conda create -p ./env python=3.10 -y) || \
(echo "Warning: Neither mamba nor conda found, creating venv instead" && python3 -m venv ./env)

# Step 2: Upgrade pip
echo "[2/7] Upgrading pip..."
./env/bin/python -m pip install --upgrade pip

# Step 3: Install from environment.yml if available
echo "[3/7] Installing from environment.yml..."
(command -v mamba >/dev/null 2>&1 && mamba env update -p ./env -f repo/PepFlowww/environment.yml) || \
(command -v conda >/dev/null 2>&1 && conda env update -p ./env -f repo/PepFlowww/environment.yml) || \
echo "Warning: Could not update from environment.yml, installing essential packages manually"

# Step 4: Install core scientific packages
echo "[4/7] Installing core scientific packages..."
./env/bin/pip install numpy pandas matplotlib biopython

# Step 5: Install additional dependencies
echo "[5/7] Installing additional dependencies..."
./env/bin/pip install joblib lmdb easydict

# Step 6: Install loguru
echo "[6/7] Installing loguru..."
./env/bin/pip install loguru

# Step 7: Install fastmcp
echo "[7/7] Installing fastmcp..."
./env/bin/pip install --ignore-installed fastmcp

echo ""
echo "=== PepFlowww MCP Setup Complete ==="
echo "Note: Download data and pretrained weights from:"
echo "https://drive.google.com/drive/folders/1bHaKDF3uCDPtfsihjZs0zmjwF6UU1uVl"
echo "To run the MCP server: ./env/bin/python src/server.py"
