# Release Notes — 2.8.0 (versionCode 12)

Covers everything since the last Play Store release (2.6.1 / versionCode 9):
internal releases 2.6.2 and 2.7.0, plus the 2.8.0 framework upgrade.

---

## Play Store "What's new" (ready to paste, under 500 chars)

```
NEW
• Set your own agenda points to win (1–10) — tap the gold "TO WIN" badge
• Keep Playing: dismiss the win screen and continue after a mis-tap
• Custom dice — roll anything from d2 to d100
• Fewer log entries: rapid taps on counters now log once

FIXED
• Android back button asks before leaving a game instead of closing the app
• Slimmer app: removed unneeded permissions

UNDER THE HOOD
• Major engine upgrade (React Native 0.85 / Expo SDK 56) for speed and longevity
```

---

## GitHub release notes (longer form)

### ✨ New features (2.7.0)

- **Configurable win target** — tap the gold "N TO WIN" badge on any agenda
  ladder to open a picker and set the agenda points needed to win (1–10,
  default 7). The win check, ladder segments, and game log all follow it.
- **Keep Playing** — the win overlay now has a "▶ KEEP PLAYING" button to
  dismiss an accidental win (e.g. a mis-tap to 7). The auto-win stays
  suppressed until both scores drop back below the target.
- **Custom dice** — the dice sheet gains a face-count stepper: roll anything
  from a d2 to a d100, alongside the standard dice and mark roll.
- **Batched tap logging** — rapid taps on agenda ladders and opponent chips
  commit as one log entry ("Agenda +3 → 5") instead of flooding the game log,
  while the displayed count still updates per tap.
- **Android back button safety** — pressing back in-game offers
  *Back to Setup* or *Quit* instead of silently killing the app; on the setup
  screen it asks before quitting.
- **Setup polish** — fox logo in the header; in solo mode the corp panel no
  longer auto-flips upside down (it only flips in two-player face-to-face
  mode).
- **UI alignment** — the "TO WIN" badge now matches the agenda tug-of-war
  column width in both portrait and landscape.

### 🔧 Maintenance

- **2.8.0:** upgraded Expo SDK 52 → 56 (React Native 0.76 → 0.85, React 18 →
  19, TypeScript 6). No user-facing changes; keeps the app current with the
  New Architecture and latest Android requirements.
- **2.6.2:** trimmed unused Android permissions (INTERNET, storage, etc.) —
  the app requests only VIBRATE and WAKE_LOCK.
- CI now auto-builds the Play Store AAB on version tags.
- Licensed under Apache-2.0 with a fan-content notice.
