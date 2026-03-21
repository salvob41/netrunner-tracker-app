"""
Entry point for the Netrunner Tracker.

Desktop run (from project root):
  python src/main.py

Android APK build (from project root):
  flet build apk

macOS app build (from project root):
  flet build macos
"""

import flet as ft
from tracker import NetrunnerTracker


def main(page: ft.Page) -> None:
    NetrunnerTracker(page)


ft.run(main, assets_dir="assets")
