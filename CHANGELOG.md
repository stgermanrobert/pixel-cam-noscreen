# Changelog

## 1.0.0 — 2026-10-25

First public release.

- Camera preview, recording (MP4/MKV) and phone-screen mirroring over USB, built on scrcpy.
- Cameras, zoom ranges and frame rates detected from the phone (`scrcpy --list-cameras`).
- Live setting changes: the preview reopens in the same place with the new settings.
- "Send to Meet / Zoom" through the OBS Virtual Camera driver, without opening OBS.
- Settings window: PIN/password (encrypted with Windows DPAPI), automatic unlock, keep-screen-awake, adb/scrcpy paths, videos folder, language.
- English and Spanish interface.
- Broken-screen rescue guide (TalkBack + keyboard + Wireless debugging).
