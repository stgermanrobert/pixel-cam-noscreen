"""Unit tests for the platform-independent parts. Run: python -m unittest discover tests"""
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pixelcam import config, i18n  # noqa: E402
from pixelcam.cameras import default_fps, parse_cameras, zoom_presets  # noqa: E402
from pixelcam.device import Device  # noqa: E402

PIXEL_8_PRO = """scrcpy 5.0.1 <https://github.com/Genymobile/scrcpy>
INFO: ADB device found:
[server] INFO: Device: [Google] google Pixel 8 Pro (Android 16)
[server] INFO: List of cameras:
    --camera-id=0    (back, 4080x3072, fps={15, 24, 30, 60}, zoom-range=[0.49, 30])
    --camera-id=1    (front, 3440x2448, fps={15, 24, 30, 60}, zoom-range=[0.9, 10])
"""

OLDER_PHONE = """[server] INFO: List of cameras:
    --camera-id=0    (back, 4000x3000, fps=[15, 30])
    --camera-id=1    (front, 3264x2448, fps=[15, 30])
    --camera-id=2    (external, 1920x1080, fps=[30])
"""


class CameraParsing(unittest.TestCase):
    def test_pixel_8_pro(self):
        cams = parse_cameras(PIXEL_8_PRO)
        self.assertEqual([c.id for c in cams], ["0", "1"])
        self.assertEqual(cams[0].facing, "back")
        self.assertEqual((cams[0].width, cams[0].height), (4080, 3072))
        self.assertEqual(cams[0].fps, [15, 24, 30, 60])
        self.assertEqual(cams[0].zoom, (0.49, 30.0))
        self.assertEqual(cams[1].zoom, (0.9, 10.0))

    def test_without_zoom_range(self):
        cams = parse_cameras(OLDER_PHONE)
        self.assertEqual(len(cams), 3)
        self.assertIsNone(cams[0].zoom)
        self.assertEqual(cams[2].facing, "external")
        self.assertEqual(cams[2].fps, [30])

    def test_nothing_to_parse(self):
        self.assertEqual(parse_cameras("ERROR: Could not find any ADB device"), [])

    def test_round_trip_dict(self):
        cam = parse_cameras(PIXEL_8_PRO)[0]
        self.assertEqual(type(cam).from_dict(cam.to_dict()), cam)

    def test_zoom_presets(self):
        self.assertEqual(zoom_presets((0.49, 30)), [0.49, 1, 2, 5, 10])
        self.assertEqual(zoom_presets((0.9, 10)), [0.9, 1, 2, 5, 10])
        self.assertEqual(zoom_presets((1, 4)), [1, 2])
        self.assertEqual(zoom_presets(None), [])

    def test_default_fps(self):
        self.assertEqual(default_fps([15, 24, 30, 60]), "30")
        self.assertEqual(default_fps([15, 24]), "24")
        self.assertEqual(default_fps([60]), "60")
        self.assertEqual(default_fps([]), "30")


class Config(unittest.TestCase):
    def test_pin_round_trip(self):
        for pin in ("1234", "my pass word", "ñandú#1"):
            enc = config.protect(pin)
            self.assertNotIn(pin, enc)
            self.assertEqual(config.unprotect(enc), pin)
        self.assertEqual(config.protect(""), "")
        self.assertEqual(config.unprotect("garbage"), "")

    def test_save_and_load_outside_project(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"APPDATA": d}):
            cfg = config.load()
            cfg["zoom"] = 0.49
            cfg["unknown_key"] = "ignored"
            config.save(cfg)
            self.assertTrue(config.config_path().startswith(d))
            loaded = config.load()
            self.assertEqual(loaded["zoom"], 0.49)
            self.assertNotIn("unknown_key", loaded)


class Translations(unittest.TestCase):
    def test_same_keys_in_every_language(self):
        en = set(i18n.STRINGS["en"])
        for code, strings in i18n.STRINGS.items():
            self.assertEqual(set(strings), en, code)


class Unlock(unittest.TestCase):
    def make_device(self, locked_states):
        dev = Device("adb")
        calls = []
        states = iter(locked_states)

        def fake_run(*args, timeout=10):
            calls.append(args)
            if args[:2] == ("shell", "dumpsys"):
                locked = next(states)
                return 0, "  mCurrentFocus=Window{1 u0 NotificationShade}\n" if locked else \
                    "  mCurrentFocus=Window{2 u0 com.google.android.apps.nexuslauncher}\n"
            return 0, ""
        dev.run = fake_run
        return dev, calls

    @mock.patch("pixelcam.device.time.sleep")
    def test_types_pin_when_locked(self, _):
        dev, calls = self.make_device([True, False])
        self.assertEqual(dev.unlock("1234"), "unlocked")
        self.assertIn(("shell", "input", "text", "1234"), calls)

    @mock.patch("pixelcam.device.time.sleep")
    def test_does_not_type_when_unlocked(self, _):
        dev, calls = self.make_device([False])
        self.assertEqual(dev.unlock("1234"), "already")
        self.assertFalse(any(c[:3] == ("shell", "input", "text") for c in calls))

    @mock.patch("pixelcam.device.time.sleep")
    def test_password_with_spaces_is_escaped(self, _):
        dev, calls = self.make_device([True, False])
        dev.unlock("a b'c")
        typed = [c[3] for c in calls if c[:3] == ("shell", "input", "text")][0]
        self.assertNotIn(" ", typed)

    @mock.patch("pixelcam.device.time.sleep")
    def test_reports_failure_and_missing_pin(self, _):
        dev, _ = self.make_device([True, True])
        self.assertEqual(dev.unlock("0000"), "failed")
        dev, _ = self.make_device([True])
        self.assertEqual(dev.unlock(""), "no_pin")


if __name__ == "__main__":
    unittest.main()
