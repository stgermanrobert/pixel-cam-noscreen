"""Small Windows helpers: find scrcpy's window, read its geometry, close it gracefully."""
import sys

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    dwmapi = ctypes.windll.dwmapi
    WM_CLOSE = 0x0010
    DWMWA_EXTENDED_FRAME_BOUNDS = 9
    _EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def windows_of(pid):
        """Visible top-level windows owned by a process."""
        found = []

        def cb(hwnd, _):
            p = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
            if p.value == pid and user32.IsWindowVisible(hwnd):
                found.append(hwnd)
            return True

        user32.EnumWindows(_EnumWindowsProc(cb), 0)
        return found

    def client_geometry(hwnd):
        """Screen position and size of the window's content area (no title bar or borders)."""
        r = wintypes.RECT()
        user32.GetClientRect(hwnd, ctypes.byref(r))
        pt = wintypes.POINT(0, 0)
        user32.ClientToScreen(hwnd, ctypes.byref(pt))
        return pt.x, pt.y, r.right - r.left, r.bottom - r.top

    def frame_bounds(hwnd):
        """Visible window rectangle (what the screen capture returns)."""
        r = wintypes.RECT()
        dwmapi.DwmGetWindowAttribute(hwnd, DWMWA_EXTENDED_FRAME_BOUNDS, ctypes.byref(r), ctypes.sizeof(r))
        return r.left, r.top, r.right - r.left, r.bottom - r.top

    def close_window(hwnd):
        """Same as clicking the X: lets scrcpy finish writing the video file."""
        user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)

    def thread_dpi_aware():
        """Use real pixels in this thread (needed to match screen-capture coordinates)."""
        try:
            user32.SetThreadDpiAwarenessContext.restype = ctypes.c_void_p
            user32.SetThreadDpiAwarenessContext(ctypes.c_void_p(-4))  # PER_MONITOR_AWARE_V2
        except Exception:
            pass

else:  # Stubs so the package can be imported (and tested) on other systems
    def windows_of(pid):
        return []

    def client_geometry(hwnd):
        return 0, 0, 0, 0

    def frame_bounds(hwnd):
        return 0, 0, 0, 0

    def close_window(hwnd):
        pass

    def thread_dpi_aware():
        pass
