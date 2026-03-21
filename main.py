"""
Entry point for the Netrunner Tracker.

Minimal by design — swapping the UI framework or build target means
changing only this file.

Desktop run:
  python main.py

Android APK build:
  flet build apk --project "Netrunner Tracker"
"""

import flet as ft
from tracker import NetrunnerTracker


def main(page: ft.Page) -> None:
    NetrunnerTracker(page)


# assets_dir tells Flet where to serve static files from.
# The NSG SVG icons are copied there so both desktop and Android
# builds can reference them with a simple "/filename.svg" path.
ft.run(main, assets_dir="assets")
