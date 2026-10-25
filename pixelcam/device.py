"""Finding adb/scrcpy and talking to the phone over USB (adb -d)."""
import glob
import os
import shlex
import shutil
import subprocess
import sys
import time

NOWIN = 0x08000000 if sys.platform == "win32" else 0  # CREATE_NO_WINDOW


def _first_file(paths):
    for p in paths:
        if p and os.path.isfile(p):
            return p
    return None


def find_scrcpy(configured=""):
    if configured and os.path.isfile(configured):
        return configured
    p = shutil.which("scrcpy")
    if p:
        return p
    la = os.environ.get("LOCALAPPDATA", "")
    cands = [os.path.join(la, "Microsoft", "WinGet", "Links", "scrcpy.exe")]
    cands += glob.glob(os.path.join(la, "Microsoft", "WinGet", "Packages", "Genymobile.scrcpy*", "**", "scrcpy.exe"),
                       recursive=True)
    cands += glob.glob(os.path.join(os.path.expanduser("~"), "scoop", "apps", "scrcpy", "current", "scrcpy.exe"))
    return _first_file(cands)


def find_adb(configured="", scrcpy_path=None):
    """Prefer an adb the user already uses, so scrcpy and the terminal share one adb server."""
    if configured and os.path.isfile(configured):
        return configured
    p = shutil.which("adb")
    if p:
        return p
    la = os.environ.get("LOCALAPPDATA", "")
    cands = [
        r"C:\platform-tools\adb.exe",
        os.path.join(la, "Android", "Sdk", "platform-tools", "adb.exe"),
    ]
    if scrcpy_path:  # scrcpy for Windows ships its own adb.exe
        cands.append(os.path.join(os.path.dirname(os.path.realpath(scrcpy_path)), "adb.exe"))
        cands += glob.glob(os.path.join(la, "Microsoft", "WinGet", "Packages", "Genymobile.scrcpy*", "**", "adb.exe"),
                           recursive=True)
    return _first_file(cands)


class Device:
    """The phone connected over USB. All commands use `adb -d` (USB only)."""

    def __init__(self, adb_path):
        self.adb_path = adb_path

    def run(self, *args, timeout=10):
        if not self.adb_path:
            return 1, ""
        try:
            r = subprocess.run([self.adb_path, "-d", *args], capture_output=True, text=True,
                               timeout=timeout, creationflags=NOWIN, errors="replace")
            return r.returncode, r.stdout
        except Exception as e:
            return 1, str(e)

    def is_connected(self):
        rc, out = self.run("get-state", timeout=5)
        return rc == 0 and out.strip() == "device"

    def model(self):
        rc, out = self.run("shell", "getprop", "ro.product.model", timeout=5)
        return out.strip() if rc == 0 and out.strip() else "Android"

    def is_locked(self):
        """Heuristic: while the keyguard is showing, the focused window is the NotificationShade.
        Works on recent Android versions (tested on Android 16); may need tweaks elsewhere."""
        _, out = self.run("shell", "dumpsys", "window")
        return any("mCurrentFocus" in l and "NotificationShade" in l for l in out.splitlines())

    def wake(self):
        self.run("shell", "input", "keyevent", "KEYCODE_WAKEUP")

    def set_stay_awake(self, on):
        self.run("shell", "svc", "power", "stayon", "usb" if on else "false")

    def unlock(self, pin):
        """Returns 'unlocked', 'already', 'no_pin' or 'failed'."""
        self.wake()
        time.sleep(0.5)
        if not self.is_locked():
            return "already"
        if not pin:
            return "no_pin"
        self.run("shell", "input", "keyevent", "82")  # bring up the PIN pad
        time.sleep(1)
        # `input text` runs in the phone's shell: quote it, and spaces must be sent as %s
        self.run("shell", "input", "text", shlex.quote(pin.replace(" ", "%s")))
        self.run("shell", "input", "keyevent", "66")  # Enter
        time.sleep(2)
        return "failed" if self.is_locked() else "unlocked"
