"""Virtual camera: copies scrcpy's camera window into the 'OBS Virtual Camera' driver (OBS itself stays closed).

Optional dependencies: pyvirtualcam, windows-capture, opencv-python, numpy (see requirements.txt).
"""
import threading
import time

from . import winapi
from .i18n import t

VCAM_W, VCAM_H, VCAM_FPS = 1280, 720, 30
PIP_PACKAGES = "pyvirtualcam windows-capture opencv-python numpy"


class VirtualCam:
    def __init__(self, get_hwnd, log):
        # Imported here so the rest of the app works without these libraries
        import cv2
        import numpy as np
        import pyvirtualcam
        from windows_capture import WindowsCapture
        self.np, self.cv2, self.pvc, self.WC = np, cv2, pyvirtualcam, WindowsCapture
        self.get_hwnd = get_hwnd
        self.log = log
        self.lock = threading.Lock()
        self.latest = np.zeros((VCAM_H, VCAM_W, 3), np.uint8)
        self.running = False
        self.cur_hwnd = None
        self.cam = None

    def start(self):
        self.cam = self.pvc.Camera(VCAM_W, VCAM_H, VCAM_FPS, fmt=self.pvc.PixelFormat.BGR, backend="obs")
        self.running = True
        threading.Thread(target=self._send_loop, daemon=True).start()
        threading.Thread(target=self._capture_loop, daemon=True).start()

    def stop(self):
        self.running = False

    # Sends the latest frame at a steady rate. While scrcpy restarts, the last image stays frozen.
    def _send_loop(self):
        try:
            while self.running:
                with self.lock:
                    frame = self.latest
                self.cam.send(frame)
                self.cam.sleep_until_next_frame()
        except Exception as e:
            self.log(t("vcam_stopped", err=e))
            self.running = False
        finally:
            try:
                self.cam.close()
            except Exception:
                pass

    # Follows scrcpy's window: when it is reopened (settings changed), capture the new one.
    def _capture_loop(self):
        winapi.thread_dpi_aware()
        ctrl = None
        while self.running:
            hwnd = self.get_hwnd()
            if hwnd != self.cur_hwnd:
                if ctrl:
                    try:
                        ctrl.stop()
                    except Exception:
                        pass
                    ctrl = None
                self.cur_hwnd = hwnd
                if hwnd:
                    ctrl = self._start_capture(hwnd)
            time.sleep(0.3)
        if ctrl:
            try:
                ctrl.stop()
            except Exception:
                pass

    def _start_capture(self, hwnd):
        def make(border):
            cap = self.WC(cursor_capture=False, draw_border=border, window_hwnd=int(hwnd))

            @cap.event
            def on_frame_arrived(frame, control):
                if not self.running or self.cur_hwnd != hwnd:
                    control.stop()
                    return
                try:
                    self._process(frame.frame_buffer, hwnd)
                except Exception:
                    pass

            @cap.event
            def on_closed():
                pass

            return cap.start_free_threaded()

        err = None
        for border in (False, None):  # hiding the yellow capture border is not supported everywhere
            try:
                return make(border)
            except Exception as e:
                err = e
        self.log(t("vcam_capture_error", err=err))
        return None

    def _crop_box(self, hwnd, fw, fh):
        """Where the image sits inside the captured window (drops title bar and borders)."""
        cx, cy, cw, ch = winapi.client_geometry(hwnd)
        ex, ey, ew, eh = winapi.frame_bounds(hwnd)
        if abs(ew - fw) <= 2 and abs(eh - fh) <= 2:
            x0, y0 = cx - ex, cy - ey
        else:  # fallback: equal side borders, title bar on top
            x0 = max(0, (fw - cw) // 2)
            y0 = max(0, fh - ch - x0)
        x0, y0 = max(0, x0), max(0, y0)
        cw, ch = min(cw, fw - x0), min(ch, fh - y0)
        if cw < 16 or ch < 16:
            return 0, 0, fw, fh
        return x0, y0, cw, ch

    def _process(self, buf, hwnd):
        np, cv2 = self.np, self.cv2
        fh, fw = buf.shape[:2]
        x0, y0, cw, ch = self._crop_box(hwnd, fw, fh)
        img = buf[y0:y0 + ch, x0:x0 + cw, :3]  # BGRA -> BGR
        scale = min(VCAM_W / cw, VCAM_H / ch)
        nw, nh = max(1, int(cw * scale)), max(1, int(ch * scale))
        small = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR)
        out = np.zeros((VCAM_H, VCAM_W, 3), np.uint8)  # letterbox (e.g. portrait image -> black bars)
        ox, oy = (VCAM_W - nw) // 2, (VCAM_H - nh) // 2
        out[oy:oy + nh, ox:ox + nw] = small
        with self.lock:
            self.latest = out
