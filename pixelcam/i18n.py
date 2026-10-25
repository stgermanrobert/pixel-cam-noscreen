"""Tiny translation layer (English / Spanish)."""
import locale
import sys

LANGS = {"en": "English", "es": "Español"}

STRINGS = {
    "en": {
        "searching": "Looking for a phone...",
        "connected": "● {model} connected via USB",
        "disconnected": "○ No phone connected over USB",
        "camera": "Camera",
        "lens": "Lens",
        "redetect": "Detect cameras again",
        "loading_cams": "Detecting cameras...",
        "zoom": "Zoom",
        "no_zoom": "This camera does not report a zoom range",
        "image": "Image",
        "rotation": "Rotation",
        "mirror": "Mirror (preview only)",
        "resolution": "Resolution",
        "aspect": "Aspect",
        "fps": "FPS",
        "bitrate": "Bitrate (Mbps)",
        "rec_window": "Recording / window",
        "rec_audio": "Record audio from the phone microphone",
        "file": "File",
        "mkv_hint": "MKV (safer if interrupted)",
        "ontop": "Window always on top",
        "vcam": "Send to Meet / Zoom  (shows up as \"OBS Virtual Camera\")",
        "btn_preview": "▶  Preview",
        "btn_record": "●  Record",
        "btn_stop": "■  Stop",
        "btn_screen": "Show phone screen",
        "btn_unlock": "Unlock",
        "btn_folder": "Open folder",
        "btn_settings": "⚙  Settings",
        "recording": "● REC  {t}",
        "win_camera": "{model} - Camera",
        "win_recording": "REC - {model}",
        "no_scrcpy": "scrcpy not found. Install it with:\nwinget install Genymobile.scrcpy\n\nor set its path in Settings.",
        "no_adb": "adb not found. Install Android platform-tools (or scrcpy, which bundles it), or set its path in Settings.",
        "no_device": "No phone found over USB.",
        "busy": "Something is already running. Press Stop first.",
        "unlocking": "Unlocking...",
        "unlocked": "Unlocked.",
        "still_locked": "Still locked: check the PIN in Settings.",
        "already_unlocked": "The phone is already unlocked.",
        "no_pin": "Set your PIN in Settings to unlock the phone automatically.",
        "live_rec": "Recording: changes will apply to the next recording.",
        "saved": "Video saved: {path}",
        "closed_itself": "scrcpy exited on its own (code {code}). Last lines:",
        "forced": "Not responding, forcing close.",
        "start_error": "Could not start scrcpy: {err}",
        "cams_found": "{n} camera(s) detected.",
        "cams_error": "Could not list the cameras (camera mirroring needs Android 12+).",
        "missing_lib": "A library is missing ({err}).\n\nRun this in PowerShell (already copied to the clipboard):\n\n{cmd}\n\nThen reopen Pixel Cam.",
        "vcam_open_error": "Could not open the OBS Virtual Camera:\n{err}\n\nIf OBS is running with 'Start Virtual Camera', stop it and try again. If OBS is not installed, install it once to get the driver.",
        "vcam_on": "Virtual camera on: pick 'OBS Virtual Camera' in Meet / Zoom.",
        "vcam_off": "Virtual camera off.",
        "vcam_stopped": "Virtual camera stopped: {err}",
        "vcam_capture_error": "Could not capture the camera window: {err}",
        "confirm_quit": "A camera or recording is open. Stop it and quit?",
        "using_adb": "adb: {path}",
        "using_scrcpy": "scrcpy: {path}",
        # Settings
        "settings": "Settings",
        "language": "Language",
        "lang_auto": "Automatic",
        "lock_section": "Screen lock",
        "pin": "PIN / password",
        "show": "Show",
        "auto_unlock": "Unlock automatically before each action",
        "pin_note": "Stored encrypted for your Windows user (DPAPI), never in the project folder.\nPattern locks are not supported.",
        "test_unlock": "Test unlock",
        "stay_awake": "Keep the phone screen on while it is plugged in",
        "paths": "Paths",
        "auto_hint": "empty = detect automatically",
        "outdir": "Videos folder",
        "save": "Save",
        "cancel": "Cancel",
        "restart_lang": "The language will change the next time you open the app.",
    },
    "es": {
        "searching": "Buscando teléfono...",
        "connected": "● {model} conectado por USB",
        "disconnected": "○ Ningún teléfono conectado por USB",
        "camera": "Cámara",
        "lens": "Lente",
        "redetect": "Detectar cámaras otra vez",
        "loading_cams": "Detectando cámaras...",
        "zoom": "Zoom",
        "no_zoom": "Esta cámara no informa un rango de zoom",
        "image": "Imagen",
        "rotation": "Rotación",
        "mirror": "Espejo (solo vista previa)",
        "resolution": "Resolución",
        "aspect": "Formato",
        "fps": "FPS",
        "bitrate": "Bitrate (Mbps)",
        "rec_window": "Grabación / ventana",
        "rec_audio": "Grabar audio del micrófono del teléfono",
        "file": "Archivo",
        "mkv_hint": "MKV (más seguro si se corta)",
        "ontop": "Ventana siempre encima",
        "vcam": "Enviar a Meet / Zoom  (aparece como \"OBS Virtual Camera\")",
        "btn_preview": "▶  Vista previa",
        "btn_record": "●  Grabar",
        "btn_stop": "■  Detener",
        "btn_screen": "Ver pantalla del teléfono",
        "btn_unlock": "Desbloquear",
        "btn_folder": "Abrir carpeta",
        "btn_settings": "⚙  Ajustes",
        "recording": "● GRABANDO  {t}",
        "win_camera": "{model} - Cámara",
        "win_recording": "GRABANDO - {model}",
        "no_scrcpy": "No encuentro scrcpy. Instálalo con:\nwinget install Genymobile.scrcpy\n\no indica su ruta en Ajustes.",
        "no_adb": "No encuentro adb. Instala Android platform-tools (o scrcpy, que lo incluye), o indica su ruta en Ajustes.",
        "no_device": "No encuentro el teléfono por USB.",
        "busy": "Ya hay algo abierto. Pulsa Detener primero.",
        "unlocking": "Desbloqueando...",
        "unlocked": "Desbloqueado.",
        "still_locked": "Sigue bloqueado: revisa el PIN en Ajustes.",
        "already_unlocked": "El teléfono ya está desbloqueado.",
        "no_pin": "Configura tu PIN en Ajustes para desbloquear el teléfono automáticamente.",
        "live_rec": "Grabando: los cambios se aplicarán en la próxima grabación.",
        "saved": "Vídeo guardado: {path}",
        "closed_itself": "scrcpy se cerró solo (código {code}). Últimas líneas:",
        "forced": "No respondió, forzando cierre.",
        "start_error": "Error al iniciar scrcpy: {err}",
        "cams_found": "{n} cámara(s) detectada(s).",
        "cams_error": "No pude listar las cámaras (la cámara por scrcpy requiere Android 12+).",
        "missing_lib": "Falta una librería ({err}).\n\nEjecuta esto en PowerShell (ya está copiado al portapapeles):\n\n{cmd}\n\nLuego reabre Pixel Cam.",
        "vcam_open_error": "No pude abrir la OBS Virtual Camera:\n{err}\n\nSi OBS está abierto con 'Start Virtual Camera', detenla y reintenta. Si no tienes OBS, instálalo una vez para tener el driver.",
        "vcam_on": "Cámara virtual activa: elige 'OBS Virtual Camera' en Meet / Zoom.",
        "vcam_off": "Cámara virtual desactivada.",
        "vcam_stopped": "Cámara virtual detenida: {err}",
        "vcam_capture_error": "No pude capturar la ventana de la cámara: {err}",
        "confirm_quit": "Hay una cámara o grabación abierta. ¿Detener y salir?",
        "using_adb": "adb: {path}",
        "using_scrcpy": "scrcpy: {path}",
        # Ajustes
        "settings": "Ajustes",
        "language": "Idioma",
        "lang_auto": "Automático",
        "lock_section": "Bloqueo de pantalla",
        "pin": "PIN / contraseña",
        "show": "Mostrar",
        "auto_unlock": "Desbloquear automáticamente antes de cada acción",
        "pin_note": "Se guarda cifrado para tu usuario de Windows (DPAPI), nunca en la carpeta del proyecto.\nEl desbloqueo por patrón no está soportado.",
        "test_unlock": "Probar desbloqueo",
        "stay_awake": "Mantener la pantalla del teléfono encendida mientras esté enchufado",
        "paths": "Rutas",
        "auto_hint": "vacío = detectar automáticamente",
        "outdir": "Carpeta de vídeos",
        "save": "Guardar",
        "cancel": "Cancelar",
        "restart_lang": "El idioma cambiará la próxima vez que abras la app.",
    },
}

_lang = "en"


def detect():
    """Best guess of the user's language: Spanish if the OS UI is Spanish, else English."""
    try:
        if sys.platform == "win32":
            import ctypes
            lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            return "es" if (lang_id & 0x3FF) == 0x0A else "en"
    except Exception:
        pass
    loc = (locale.getlocale()[0] or "").lower()
    return "es" if loc.startswith(("es", "spanish")) else "en"


def set_language(code):
    global _lang
    _lang = code if code in STRINGS else detect()


def current():
    return _lang


def t(key, **kw):
    s = STRINGS[_lang].get(key, STRINGS["en"][key])
    return s.format(**kw) if kw else s
