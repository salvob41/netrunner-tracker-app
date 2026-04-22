#!/usr/bin/env python3
"""
Capture README mobile-style screenshots against a running local Flet web app.

  cd src && python -c "import flet as ft; from tracker import NetrunnerTracker; ..."

With project venv: pip install playwright flet && python -m playwright install chromium
Then: python scripts/capture_readme_screens.py
"""

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
BASE = "http://127.0.0.1:8550"


def _context(playwright, height: int):
    return playwright.chromium.launch().new_context(
        viewport={"width": 390, "height": height},
        device_scale_factor=2.5,
        is_mobile=True,
        has_touch=True,
        user_agent=(
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
            "Mobile/15E148 Safari/604.1"
        ),
    )


def main() -> None:
    DOCS.mkdir(exist_ok=True)
    with sync_playwright() as p:
        # 1) Start of match — phone-sized viewport
        c1 = _context(p, 844)
        p1 = c1.new_page()
        p1.goto(BASE, wait_until="networkidle", timeout=60_000)
        p1.wait_for_timeout(2500)
        p1.screenshot(path=str(DOCS / "screenshot-mobile-initial.png"), full_page=True)
        c1.close()

        # 2) Agenda + 3) log — wider canvas so the open log (below header) is visible
        c2 = _context(p, 1150)
        p2 = c2.new_page()
        p2.goto(BASE, wait_until="networkidle", timeout=60_000)
        p2.wait_for_timeout(2500)
        w, h = p2.viewport_size["width"], p2.viewport_size["height"]
        for _ in range(3):
            p2.mouse.click(w * 0.88, h * 0.25)
            p2.wait_for_timeout(100)
        for _ in range(2):
            p2.mouse.click(w * 0.88, h * 0.48)
            p2.wait_for_timeout(100)
        p2.wait_for_timeout(300)
        p2.screenshot(path=str(DOCS / "screenshot-mobile-agenda.png"), full_page=True)
        p2.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
        p2.wait_for_timeout(300)
        p2.mouse.click(w * 0.5, h - 42)
        p2.wait_for_timeout(700)
        p2.screenshot(path=str(DOCS / "screenshot-mobile-logs.png"), full_page=True)
        c2.close()


if __name__ == "__main__":
    main()
