# Rescuing an Android phone with a dead screen

[Español](rescue-guide.es.md) · [Back to README](../README.md)

Your phone's screen is black (or touch no longer works), but the phone is still on. This guide gets you **full control of it from a Windows PC** — see its screen, use it with mouse and keyboard, back it up, and use it as a camera with Pixel Cam.

It is written from a real case: a **Google Pixel 8 Pro on Android 16** whose touch failed first and then the display went black. Steps marked *(untested)* are reasonable but were not needed in that case.

> **Why is this hard?** Android only lets a PC control the phone (ADB) if **USB debugging** is on **and** you tapped *"Allow"* on the phone for that PC. That confirmation is a security feature: without it, anyone with a cable could get into a stolen phone. There is no way around it — but there are other ways to "see" and "tap" the phone.

---

## 1. Is the phone alive?

- **Call it** from another phone: does it ring or vibrate?
- **Force restart:** hold the **power button ~30 seconds** until it vibrates.
- **Ask ADB.** Install Android platform-tools (or scrcpy, which includes `adb`):
  ```powershell
  winget install Genymobile.scrcpy
  ```
  Close and reopen PowerShell, plug the phone in by USB and run:
  ```powershell
  adb devices
  ```

| Result | Meaning | Go to |
|---|---|---|
| `XXXXXXXX  device` | On, USB debugging enabled, this PC authorized. You're done here. | [Step 4](#4-make-it-permanent) |
| `XXXXXXXX  unauthorized` | On and **USB debugging is enabled**, but this PC was never allowed. | [Step 2](#2-unauthorized-get-access-with-talkback--keyboard--wireless-debugging) |
| Empty list | Off, or USB debugging is disabled. | Check Device Manager when plugging in; try [Step 3](#3-other-routes) |

> If the battery was fully drained (e.g. months in a drawer), charge it for a while first. If the back is **bulging** or the screen is lifting, unplug it: a swollen battery is dangerous.

---

## 2. `unauthorized`: get access with TalkBack + keyboard + Wireless debugging

The idea: **TalkBack** (Android's screen reader) reads the screen aloud, a **USB keyboard** lets you move around, and **Wireless debugging** lets you pair the PC over Wi-Fi with a code that TalkBack reads to you. No touch screen needed.

What you need: a USB keyboard + a USB-C OTG adapter (or a USB-C keyboard), and the phone on a Wi-Fi network the PC is also on.

### 2.1 Turn on TalkBack (your "eyes")

With **nothing plugged in**, try in this order:
1. Say **"Hey Google, turn on TalkBack"**.
2. Or hold **both volume buttons for 3 seconds** (only works if the accessibility shortcut was set up; it may ask you to repeat it to confirm).

It worked if the phone starts **talking**. TalkBack speaks in the phone's language.

### 2.2 Unlock with the keyboard

1. Plug the keyboard into the phone.
2. Press the phone's **power button once** and wait until TalkBack says something (time, lock screen…). If it says *"screen off"*, press it once more.
3. **Type your PIN** on the keyboard and press **Enter**.
4. Press **Tab** a few times: if TalkBack mentions apps or the home screen, it is unlocked (it may say *"device unlocked"*).

Keyboard navigation: **Tab / Shift+Tab** move between items, **Enter** activates. If Tab doesn't move, try **Alt + arrows** and **Alt+Enter** (TalkBack's own shortcuts).

### 2.3 Turn on Wireless debugging

1. Say **"Hey Google, turn off airplane mode"** and **"Hey Google, turn on Wi-Fi"** if needed.
2. Say **"Hey Google, open developer options"** (or open Settings → System → Developer options with the keyboard).
3. Tab to **Wireless debugging** and turn it on; accept *"Allow on this network"*. TalkBack should read the switch as **ON**.
4. Go into **Wireless debugging** → **Pair device with pairing code**. TalkBack reads a **6-digit code** (often as a number: *"one hundred twenty-three thousand…"*) and an IP:port. **Leave this dialog open.**

### 2.4 Pair from the PC

You don't need to understand the IP or port by ear — the PC can find them:

```powershell
adb mdns services
```

You'll see lines like:

```
adb-XXXXXXXX-xxxx   _adb-tls-pairing._tcp   192.168.1.50:41393
adb-XXXXXXXX-xxxx   _adb-tls-connect._tcp   192.168.1.50:45435
```

- `_adb-tls-pairing` → port for **pairing** (only shown while the pairing dialog is open).
- `_adb-tls-connect` → port for **connecting**.

```powershell
adb pair 192.168.1.50:41393 123456      # pairing port + the 6-digit code
adb connect 192.168.1.50:45435          # connect port
adb devices
```

Notes from the real case:
- Using the **connect** port with `adb pair` fails with `protocol fault`. Use the **pairing** one.
- The **code changes** each time you reopen the dialog. If it fails, reopen it, listen again (Shift+Tab then Tab repeats the item) and run `adb mdns services` again.

### 2.5 See the screen

```powershell
scrcpy
```

You now see the phone on your PC and control it with mouse and keyboard. First thing: **turn TalkBack off** (*"Hey Google, turn off TalkBack"*), because with TalkBack on, clicks behave differently.

---

## 3. Other routes

**USB-C video output** — Pixel 8, 8 Pro and 8a can output video over USB-C (DisplayPort Alt Mode) since the June 2024 feature drop. With a **USB-C hub that has HDMI + USB ports + power delivery**, you can plug in a TV/monitor, a mouse and a keyboard at the same time and use the phone normally. Notes:
- It must be a real **DP Alt Mode** adapter. USB "graphics card" adapters that need a driver (DisplayLink-style, e.g. USB-A to HDMI) **do not work**.
- When a display is connected the phone may ask on its own screen whether to mirror; you may have to accept it blind with the keyboard *(untested)*.

**A PC that was already authorized** — authorization is tied to the files `%USERPROFILE%\.android\adbkey` and `adbkey.pub` on the PC. If another computer was ever authorized ("Always allow"), copy those two files to the same folder on this PC, then run `adb kill-server` and `adb devices`.

**USB debugging was never enabled** *(untested)* — with TalkBack + keyboard you could in theory go to Settings → About phone, press Enter **7 times** on *Build number* to enable Developer options, then continue with [2.3](#23-turn-on-wireless-debugging). If TalkBack can't be turned on either, the realistic option is to **replace the screen**.

**Things that won't work** — bypassing the ADB authorization prompt (by design), and unlocking the bootloader (requires *OEM unlocking* enabled beforehand and **wipes all data**).

---

## 4. Make it permanent

Do this now, while you have control:

1. **Authorize USB for good:** plug the phone into the PC by USB. In the scrcpy window the dialog *"Allow USB debugging?"* appears: check **"Always allow from this computer"** and tap **Allow**. Wireless debugging turns off on every reboot; USB authorization stays.
2. **Disable adb authorization timeout** in Developer options, so the authorization doesn't expire after 7 days without connecting.
3. **Back up the PC's keys** (`%USERPROFILE%\.android\adbkey` and `adbkey.pub`) somewhere safe and private. If you reinstall Windows, copy them back and the phone still recognizes you. `adbkey` is a private key: don't share it.
4. **Back up the phone** (photos, 2FA apps) while you can see it.

From now on, with the cable plugged in, `scrcpy` (or Pixel Cam) works directly — no Wi-Fi, no TalkBack.

---

## 5. Use it as a camera

Open [Pixel Cam](../README.md), set your PIN in Settings, and you're done.

Alternatively, Android 14+ has a built-in **Webcam** USB mode (USB notification → *Webcam*), which Windows sees as a normal camera without extra software. It's simpler, but you lose Pixel Cam's lens, zoom and rotation controls.
