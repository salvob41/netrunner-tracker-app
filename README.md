# Netrunner Game Tracker

A game state tracker for [Android: Netrunner](https://nullsignal.games/), built with [Flet](https://flet.dev/) (Flutter for Python).

**[Try it in your browser](https://salvob41.github.io/netrunner-tracker-app/)**

## Features

- **Turn tracking** — Corp/Runner turn indicator with round counter
- **Click tokens** — tap to spend, tap to restore
- **Credits** — debounced +/- with batched log entries
- **Agenda score** — split pip display with score above each side
- **Tags & Core Damage** — compact side-by-side layout
- **Hand Size** — tracks max hand size (base 5 - core damage + bonuses)
- **Optional stats** — Bad Pub, Memory Units, Link (toggle on/off as needed)
- **Game log** — timestamped event log with NSG icons, collapsible panel
- **Cross-platform** — runs on Android (APK), web (GitHub Pages), and desktop

## Screenshots

The app uses official [Null Signal Games](https://nullsignal.games/) iconography, tinted per-faction using `SRC_IN` blend mode.

## Running locally

```bash
# Install dependencies
pip install flet

# Run desktop app
cd src && python main.py

# Run as web app (opens browser)
cd src && python -c "
import flet as ft
from tracker import NetrunnerTracker
def main(page): NetrunnerTracker(page)
ft.run(main, assets_dir='assets', view=ft.AppView.WEB_BROWSER, port=8550)
"
```

## Building

```bash
# Android APK
flet build apk

# Web (static files in build/web/)
flet build web

# macOS app
flet build macos
```

## Project structure

```
src/
├── main.py          # Entry point
├── tracker.py       # Controller — wires GameState to Flet UI
├── state.py         # Pure game state model (no UI imports)
├── components.py    # Reusable UI widgets
├── theme.py         # Colors, asset paths, symbols
├── game_log.py      # Event log system
└── assets/          # NSG PNG icons (tinted at runtime)
```

**Architecture**: State is fully decoupled from UI. `state.py` has zero Flet imports — it's testable and can support save/load or undo without touching widgets.

## CI/CD

GitHub Actions workflows run on push to `main`:

- **Build APK** — builds Android APK, uploads as downloadable artifact
- **Deploy Web** — builds static web app and deploys to GitHub Pages

## Credits

- Game design: [Null Signal Games](https://nullsignal.games/) (formerly NISEI / Fantasy Flight Games)
- Icons: [NSG Visual Assets](https://nullsignal.games/about/resources/)
- Built with: [Flet](https://flet.dev/)

## License

This project is a fan-made utility. Android: Netrunner is a trademark of Fantasy Flight Games / Null Signal Games.
