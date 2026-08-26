#!/usr/bin/env python3
"""Standalone launcher for building the E++ binary with PyInstaller.

Build (from the repo root):
    pip install pyinstaller
    python -m PyInstaller --onefile --name epp run_epp.py --noconfirm

Result: dist/epp  (dist/epp.exe on Windows)
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from interpreter.epp import main

if __name__ == '__main__':
    main()
