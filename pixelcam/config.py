"""Settings storage. Lives in %APPDATA%\\pixel-cam-noscreen, never inside the project folder."""
import base64
import json
import os
import sys

from . import APP_ID

DEFAULTS = {
    # Camera / image
    "camera_id": "0",
    "zoom": 1.0,
    "rot": "0",
    "mirror": False,
    "res": "1080p",
    "ar": "16:9",
    "fps": "30",
    "bitrate": 20,
    "audio": True,
    "ontop": False,
    "ext": "mp4",
    # App
    "language": "auto",
    "pin_enc": "",
    "auto_unlock": True,
    "stay_awake": True,
    "adb_path": "",
    "scrcpy_path": "",
    "outdir": os.path.join(os.path.expanduser("~"), "Videos", "Pixel Cam"),
    "cameras_cache": {},
}


def config_dir():
    base = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, APP_ID)


def config_path():
    return os.path.join(config_dir(), "config.json")


def load():
    cfg = dict(DEFAULTS)
    try:
        with open(config_path(), encoding="utf-8") as f:
            stored = json.load(f)
        cfg.update({k: v for k, v in stored.items() if k in DEFAULTS})
    except Exception:
        pass
    return cfg


def save(cfg):
    try:
        os.makedirs(config_dir(), exist_ok=True)
        tmp = config_path() + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        os.replace(tmp, config_path())
    except Exception:
        pass


# ---------------- PIN protection ----------------
# On Windows the PIN is encrypted with DPAPI: only the same Windows user on the same PC can read it.

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    class _Blob(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    _crypt32 = ctypes.windll.crypt32
    _kernel32 = ctypes.windll.kernel32
    _UI_FORBIDDEN = 0x1

    def _dpapi(data, encrypt):
        buf = ctypes.create_string_buffer(data, len(data))
        blob_in = _Blob(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
        blob_out = _Blob()
        fn = _crypt32.CryptProtectData if encrypt else _crypt32.CryptUnprotectData
        ok = fn(ctypes.byref(blob_in), None, None, None, None, _UI_FORBIDDEN, ctypes.byref(blob_out))
        if not ok:
            raise OSError("DPAPI failed")
        try:
            return ctypes.string_at(blob_out.pbData, blob_out.cbData)
        finally:
            _kernel32.LocalFree(blob_out.pbData)


def protect(text):
    if not text:
        return ""
    raw = text.encode("utf-8")
    if sys.platform == "win32":
        return "dpapi:" + base64.b64encode(_dpapi(raw, True)).decode("ascii")
    # Non-Windows fallback (the app targets Windows; this only keeps tests/other OSes working)
    return "b64:" + base64.b64encode(raw).decode("ascii")


def unprotect(value):
    if not value:
        return ""
    try:
        kind, payload = value.split(":", 1)
        data = base64.b64decode(payload)
        if kind == "dpapi" and sys.platform == "win32":
            return _dpapi(data, False).decode("utf-8")
        if kind == "b64":
            return data.decode("utf-8")
    except Exception:
        pass
    return ""
