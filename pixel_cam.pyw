"""Pixel Cam — No Screen. Double-click to open (Windows)."""
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def show_startup_error(details):
    """A .pyw has no console, so startup errors would be invisible: show them and save them to a file."""
    log_path = os.path.join(HERE, "pixel_cam_error.log")
    try:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(details)
    except Exception:
        log_path = None
    msg = "Pixel Cam could not start / no se pudo iniciar:\n\n" + details[-1500:]
    if log_path:
        msg += f"\n\nSaved to / Guardado en:\n{log_path}"
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Pixel Cam", msg)
        root.destroy()
    except Exception:
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, msg, "Pixel Cam", 0x10)
        except Exception:
            pass


if __name__ == "__main__":
    if not os.path.isdir(os.path.join(HERE, "pixelcam")):
        show_startup_error("The 'pixelcam' folder was not found next to this file.\n"
                           "Extract the whole ZIP first (right click > Extract All).\n\n"
                           "No encuentro la carpeta 'pixelcam' junto a este archivo.\n"
                           "Descomprime el ZIP completo primero (clic derecho > Extraer todo).")
        sys.exit(1)
    try:
        from pixelcam.app import main
        main()
    except Exception:
        show_startup_error(traceback.format_exc())
        sys.exit(1)
