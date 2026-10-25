"""Main window."""
import collections
import datetime
import os
import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from . import APP_NAME, __version__, config, winapi
from .cameras import Camera, default_fps, list_cameras, zoom_presets
from .device import NOWIN, Device, find_adb, find_scrcpy
from .i18n import LANGS, set_language, t
from .vcam import PIP_PACKAGES, VirtualCam

RES = {"720p": "1280", "1080p": "1920", "1440p": "2560", "4K": "3840"}
ASPECTS = ["16:9", "4:3", "1:1", "sensor"]
LIVE_DELAY_MS = 600  # wait after the last change before restarting the preview


class App:
    def __init__(self, root):
        self.root = root
        self.cfg = config.load()
        set_language(self.cfg["language"])
        root.title(APP_NAME)
        root.resizable(False, False)

        self.q = queue.Queue()
        self.proc = None
        self.busy = False            # a scrcpy is starting or running
        self.mode = None             # "preview" | "record" | "screen"
        self.user_stopped = False
        self.restart_pending = False
        self.pending_record = False
        self.live_job = None
        self.geom = None             # camera window position/size, to reopen it in the same place
        self.geom_shape = None
        self.running_shape = None
        self.rec_file = None
        self.rec_start = None
        self.connected = None
        self.model = "Android"
        self.tail = collections.deque(maxlen=15)
        self.vcam = None
        self.no_pin_warned = False

        cache = self.cfg.get("cameras_cache") or {}
        self.cameras = [Camera.from_dict(d) for d in cache.get("cams", [])]

        c = self.cfg
        self.cam_id = tk.StringVar(value=c["camera_id"])
        self.cam_label = tk.StringVar()
        self.zoom = tk.DoubleVar(value=c["zoom"])
        self.rot = tk.StringVar(value=c["rot"])
        self.mirror = tk.BooleanVar(value=c["mirror"])
        self.res = tk.StringVar(value=c["res"])
        self.ar = tk.StringVar(value=c["ar"])
        self.fps = tk.StringVar(value=c["fps"])
        self.bitrate = tk.IntVar(value=c["bitrate"])
        self.audio = tk.BooleanVar(value=c["audio"])
        self.ontop = tk.BooleanVar(value=c["ontop"])
        self.ext = tk.StringVar(value=c["ext"])
        self.vcam_on = tk.BooleanVar(value=False)

        self.resolve_tools()
        self.build()
        self.refresh_cameras()
        for v in (self.cam_id, self.zoom, self.rot, self.mirror, self.res, self.ar,
                  self.fps, self.bitrate, self.ontop):
            v.trace_add("write", self.on_setting_change)

        self.log(f"{APP_NAME} {__version__}")
        self.log(t("using_scrcpy", path=self.scrcpy) if self.scrcpy else t("no_scrcpy").splitlines()[0])
        self.log(t("using_adb", path=self.adb) if self.adb else t("no_adb"))
        if not self.pin():
            self.log(t("no_pin"))

        threading.Thread(target=self.watch_device, daemon=True).start()
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.poll()

    # ---------------- Tools ----------------
    def resolve_tools(self):
        self.scrcpy = find_scrcpy(self.cfg["scrcpy_path"])
        self.adb = find_adb(self.cfg["adb_path"], self.scrcpy)
        self.device = Device(self.adb)

    def env(self):
        env = os.environ.copy()
        if self.adb:
            env["ADB"] = self.adb  # scrcpy uses the same adb as the app (one adb server)
        return env

    def pin(self):
        return config.unprotect(self.cfg.get("pin_enc", ""))

    # ---------------- UI ----------------
    def build(self):
        f = ttk.Frame(self.root, padding=12)
        f.grid()

        top = ttk.Frame(f)
        top.grid(row=0, column=0, sticky="we", pady=(0, 8))
        self.status = ttk.Label(top, text=t("searching"), font=("Segoe UI", 10, "bold"))
        self.status.pack(side="left")
        ttk.Button(top, text=t("btn_settings"), command=self.open_settings).pack(side="right")
        self.rec_lbl = ttk.Label(top, text="", foreground="#d00000", font=("Segoe UI", 10, "bold"))
        self.rec_lbl.pack(side="right", padx=8)

        # Camera
        c = ttk.LabelFrame(f, text=t("camera"), padding=8)
        c.grid(row=1, column=0, sticky="we", pady=4)
        ttk.Label(c, text=t("lens")).grid(row=0, column=0, sticky="w")
        self.cam_combo = ttk.Combobox(c, textvariable=self.cam_label, width=34, state="readonly")
        self.cam_combo.grid(row=0, column=1, columnspan=3, sticky="w")
        self.cam_combo.bind("<<ComboboxSelected>>", self.on_cam_selected)
        ttk.Button(c, text="↻", width=3, command=self.detect_cameras).grid(row=0, column=4, sticky="w", padx=4)
        ttk.Label(c, text=t("zoom")).grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.zoom_scale = tk.Scale(c, from_=1, to=10, resolution=0.1, orient="horizontal",
                                   length=280, variable=self.zoom, showvalue=True)
        self.zoom_scale.grid(row=1, column=1, columnspan=4, sticky="we")
        self.presets = ttk.Frame(c)
        self.presets.grid(row=2, column=1, columnspan=4, sticky="w")
        self.zoom_note = ttk.Label(c, text="", foreground="#888888")
        self.zoom_note.grid(row=3, column=1, columnspan=4, sticky="w")

        # Image
        im = ttk.LabelFrame(f, text=t("image"), padding=8)
        im.grid(row=2, column=0, sticky="we", pady=4)
        ttk.Label(im, text=t("rotation")).grid(row=0, column=0, sticky="w")
        rf = ttk.Frame(im)
        rf.grid(row=0, column=1, columnspan=3, sticky="w")
        for r in ("0", "90", "180", "270"):
            ttk.Radiobutton(rf, text=f"{r}°", value=r, variable=self.rot).pack(side="left", padx=2)
        ttk.Checkbutton(im, text=t("mirror"), variable=self.mirror).grid(row=1, column=1, columnspan=3, sticky="w")
        ttk.Label(im, text=t("resolution")).grid(row=2, column=0, sticky="w", pady=2)
        ttk.Combobox(im, textvariable=self.res, values=list(RES), width=8, state="readonly").grid(
            row=2, column=1, sticky="w")
        ttk.Label(im, text=t("aspect")).grid(row=2, column=2, sticky="e", padx=(10, 4))
        ttk.Combobox(im, textvariable=self.ar, values=ASPECTS, width=7, state="readonly").grid(
            row=2, column=3, sticky="w")
        ttk.Label(im, text=t("fps")).grid(row=3, column=0, sticky="w", pady=2)
        self.fps_combo = ttk.Combobox(im, textvariable=self.fps, values=["24", "30", "60"], width=8,
                                      state="readonly")
        self.fps_combo.grid(row=3, column=1, sticky="w")
        ttk.Label(im, text=t("bitrate")).grid(row=3, column=2, sticky="e", padx=(10, 4))
        ttk.Spinbox(im, from_=4, to=80, increment=2, textvariable=self.bitrate, width=6).grid(
            row=3, column=3, sticky="w")

        # Recording / window
        g = ttk.LabelFrame(f, text=t("rec_window"), padding=8)
        g.grid(row=3, column=0, sticky="we", pady=4)
        ttk.Checkbutton(g, text=t("rec_audio"), variable=self.audio).grid(row=0, column=0, columnspan=3, sticky="w")
        ttk.Label(g, text=t("file")).grid(row=1, column=0, sticky="w")
        ttk.Radiobutton(g, text="MP4", value="mp4", variable=self.ext).grid(row=1, column=1, sticky="w")
        ttk.Radiobutton(g, text=t("mkv_hint"), value="mkv", variable=self.ext).grid(row=1, column=2, sticky="w")
        ttk.Checkbutton(g, text=t("ontop"), variable=self.ontop).grid(row=2, column=0, columnspan=3, sticky="w")
        ttk.Checkbutton(g, text=t("vcam"), variable=self.vcam_on, command=self.toggle_vcam).grid(
            row=3, column=0, columnspan=3, sticky="w", pady=(4, 0))

        # Buttons
        b = ttk.Frame(f)
        b.grid(row=4, column=0, sticky="we", pady=(8, 2))
        for text, cmd in ((t("btn_preview"), self.preview), (t("btn_record"), self.record),
                          (t("btn_stop"), self.stop)):
            ttk.Button(b, text=text, command=cmd).pack(side="left", expand=True, fill="x", padx=2)
        b2 = ttk.Frame(f)
        b2.grid(row=5, column=0, sticky="we", pady=2)
        for text, cmd in ((t("btn_screen"), self.screen), (t("btn_unlock"), self.do_unlock),
                          (t("btn_folder"), self.open_folder)):
            ttk.Button(b2, text=text, command=cmd).pack(side="left", expand=True, fill="x", padx=2)

        self.logbox = tk.Text(f, height=8, width=66, font=("Consolas", 8), state="disabled")
        self.logbox.grid(row=6, column=0, pady=(8, 0))

    def log(self, text):
        self.q.put(("log", text))

    # ---------------- Cameras ----------------
    def current_camera(self):
        for cam in self.cameras:
            if cam.id == self.cam_id.get():
                return cam
        return None

    def refresh_cameras(self):
        """Fill the lens list from self.cameras and adapt zoom/fps to the selected one."""
        if not self.cameras:
            self.cam_combo.config(values=[])
            self.cam_label.set(t("loading_cams"))
            return
        self.cam_combo.config(values=[cam.label() for cam in self.cameras])
        if not self.current_camera():
            back = [cam for cam in self.cameras if cam.facing == "back"]
            self.cam_id.set((back or self.cameras)[0].id)
        self.cam_label.set(self.current_camera().label())
        self.on_cam_change()

    def on_cam_selected(self, _=None):
        idx = self.cam_combo.current()
        if 0 <= idx < len(self.cameras):
            self.cam_id.set(self.cameras[idx].id)
            self.on_cam_change()

    def on_cam_change(self):
        cam = self.current_camera()
        if not cam:
            return
        for w in self.presets.winfo_children():
            w.destroy()
        if cam.zoom:
            zmin, zmax = cam.zoom
            self.zoom_scale.config(state="normal", from_=zmin, to=zmax)
            if not zmin <= self.zoom.get() <= zmax:
                self.zoom.set(1.0 if zmin <= 1 <= zmax else zmin)
            for z in zoom_presets(cam.zoom):
                ttk.Button(self.presets, text=f"{round(z, 1):g}x", width=5,
                           command=lambda z=z: self.zoom.set(z)).pack(side="left", padx=1)
            self.zoom_note.config(text="")
        else:
            self.zoom_scale.config(state="disabled")
            self.zoom_note.config(text=t("no_zoom"))
        fps_values = [str(x) for x in cam.fps] or ["24", "30", "60"]
        self.fps_combo.config(values=fps_values)
        if self.fps.get() not in fps_values:
            self.fps.set(default_fps(cam.fps))

    def detect_cameras(self):
        if not self.scrcpy or not self.connected:
            return
        self.log(t("loading_cams"))

        def work():
            cams, raw = list_cameras(self.scrcpy, self.env())
            self.q.put(("cams", (cams, raw)))
        threading.Thread(target=work, daemon=True).start()

    def on_cameras(self, cams, raw):
        if not cams:
            self.log(t("cams_error"))
            for line in [l for l in raw.splitlines() if l.strip()][-6:]:
                self.log("   " + line)
            return
        self.cameras = cams
        self.cfg["cameras_cache"] = {"model": self.model, "cams": [c.to_dict() for c in cams]}
        config.save(self.cfg)
        self.log(t("cams_found", n=len(cams)))
        self.refresh_cameras()

    # ---------------- Live changes ----------------
    def on_setting_change(self, *_):
        if self.live_job:
            self.root.after_cancel(self.live_job)
        self.live_job = self.root.after(LIVE_DELAY_MS, self.apply_live)

    def apply_live(self):
        """scrcpy cannot change camera settings while running, so the preview is reopened."""
        self.live_job = None
        if not self.running():
            return
        if self.mode == "record":
            self.log(t("live_rec"))
        elif self.mode == "preview":
            self.restart_pending = True
            self.stop()

    # ---------------- scrcpy ----------------
    def save_cfg(self):
        try:
            bitrate = int(self.bitrate.get())
        except (tk.TclError, ValueError):
            bitrate = 20
        self.cfg.update({
            "camera_id": self.cam_id.get(), "zoom": self.zoom.get(), "rot": self.rot.get(),
            "mirror": self.mirror.get(), "res": self.res.get(), "ar": self.ar.get(), "fps": self.fps.get(),
            "bitrate": bitrate, "audio": self.audio.get(), "ontop": self.ontop.get(), "ext": self.ext.get(),
        })
        config.save(self.cfg)

    def shape_key(self):
        return self.rot.get(), self.ar.get()

    def camera_args(self, record_file=None):
        rot = self.rot.get()
        disp = ("flip" if self.mirror.get() else "") + rot
        try:
            bitrate = int(self.bitrate.get())
        except (tk.TclError, ValueError):
            bitrate = 20
        title = t("win_recording" if record_file else "win_camera", model=self.model)
        a = ["-d", "--video-source=camera", f"--camera-id={self.cam_id.get()}",
             f"--camera-ar={self.ar.get()}", f"--camera-fps={self.fps.get()}",
             "-m", RES[self.res.get()], "-b", f"{bitrate}M",
             f"--display-orientation={disp}", "--window-title", title]
        cam = self.current_camera()
        if cam and cam.zoom:
            z = min(max(self.zoom.get(), cam.zoom[0]), cam.zoom[1])
            a.append(f"--camera-zoom={z:.2f}")
        if self.geom:
            x, y, w, h = self.geom
            a += [f"--window-x={x}", f"--window-y={y}"]
            if self.geom_shape == self.shape_key():  # same shape: keep the size too
                a += [f"--window-width={w}", f"--window-height={h}"]
        if self.ontop.get():
            a.append("--always-on-top")
        if record_file:
            a += [f"--record={record_file}", f"--record-orientation={rot}"]
            a += ["--audio-source=mic", "--no-audio-playback"] if self.audio.get() else ["--no-audio"]
        else:
            a.append("--no-audio")
        return a

    def running(self):
        return self.proc is not None and self.proc.poll() is None

    def launch(self, args, mode):
        if not self.scrcpy:
            messagebox.showerror(APP_NAME, t("no_scrcpy"))
            return False
        if not self.adb:
            messagebox.showerror(APP_NAME, t("no_adb"))
            return False
        if not self.connected:
            messagebox.showwarning(APP_NAME, t("no_device"))
            return False
        if self.busy:
            messagebox.showinfo(APP_NAME, t("busy"))
            return False
        self.busy = True
        self.mode = mode
        self.running_shape = self.shape_key()
        self.user_stopped = False
        self.tail.clear()
        self.save_cfg()
        threading.Thread(target=self._run, args=(args,), daemon=True).start()
        return True

    def _unlock(self):
        if not self.cfg.get("auto_unlock", True):
            self.device.wake()
            return
        result = self.device.unlock(self.pin())
        if result == "unlocked":
            self.log(t("unlocked"))
        elif result == "failed":
            self.log(t("still_locked"))
        elif result == "no_pin" and not self.no_pin_warned:
            self.no_pin_warned = True
            self.log(t("no_pin"))

    def _run(self, args):
        self._unlock()
        self.log("scrcpy " + " ".join(args))
        try:
            self.proc = subprocess.Popen([self.scrcpy, *args], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                         text=True, env=self.env(), creationflags=NOWIN, errors="replace")
        except Exception as e:
            self.log(t("start_error", err=e))
            self.q.put(("ended", -1))
            return
        for line in self.proc.stdout:
            line = line.rstrip()
            if not line:
                continue
            self.tail.append(line)
            if "ERROR" in line or "WARN" in line:
                self.log(line)
        self.q.put(("ended", self.proc.wait()))

    def preview(self):
        self.geom = None
        self.launch(self.camera_args(), "preview")

    def record(self):
        if self.busy:
            if self.mode == "preview":  # switch from preview to recording in one click
                self.pending_record = True
                self.stop()
            else:
                messagebox.showinfo(APP_NAME, t("busy"))
            return
        self._start_record()

    def _start_record(self):
        outdir = self.cfg["outdir"]
        os.makedirs(outdir, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        fname = os.path.join(outdir, f"pixelcam_{ts}.{self.ext.get()}")
        if self.launch(self.camera_args(fname), "record"):
            self.rec_file = fname
            self.rec_start = time.time()

    def screen(self):
        self.geom = None
        self.launch(["-d", "--stay-awake", "--window-title", self.model], "screen")

    def stop(self):
        if not self.running():
            self.restart_pending = False
            self.pending_record = False
            return
        self.user_stopped = True
        proc = self.proc
        hwnds = winapi.windows_of(proc.pid)
        if hwnds and self.mode in ("preview", "record"):
            self.geom = winapi.client_geometry(hwnds[0])
            self.geom_shape = self.running_shape
        for h in hwnds:  # like clicking the X, so the video file is finalized properly
            winapi.close_window(h)
        if not hwnds:
            subprocess.run(["taskkill", "/PID", str(proc.pid)], capture_output=True, creationflags=NOWIN)

        def force():
            for _ in range(50):
                if proc.poll() is not None:
                    return
                time.sleep(0.1)
            self.log(t("forced"))
            proc.kill()
        threading.Thread(target=force, daemon=True).start()

    def on_ended(self, code):
        self.busy = False
        if self.rec_file:
            self.log(t("saved", path=self.rec_file))
        self.rec_file = None
        self.rec_start = None
        self.rec_lbl.config(text="")
        if not self.user_stopped:
            self.log(t("closed_itself", code=code))
            for line in list(self.tail)[-8:]:
                self.log("   " + line)
            self.restart_pending = self.pending_record = False
            return
        if self.pending_record:
            self.pending_record = self.restart_pending = False
            self._start_record()
        elif self.restart_pending:
            self.restart_pending = False
            self.launch(self.camera_args(), "preview")

    # ---------------- Other actions ----------------
    def do_unlock(self):
        if not self.pin():
            self.open_settings()
            return
        if not self.connected:
            messagebox.showwarning(APP_NAME, t("no_device"))
            return

        def work():
            result = self.device.unlock(self.pin())
            self.log(t({"unlocked": "unlocked", "already": "already_unlocked",
                        "failed": "still_locked", "no_pin": "no_pin"}[result]))
        threading.Thread(target=work, daemon=True).start()

    def open_folder(self):
        os.makedirs(self.cfg["outdir"], exist_ok=True)
        os.startfile(self.cfg["outdir"])

    def open_settings(self):
        SettingsDialog(self)

    # ---------------- Device watcher ----------------
    def watch_device(self):
        while True:
            ok = self.device.is_connected()
            if ok and not self.connected:
                model = self.device.model()
                if self.cfg.get("stay_awake", True):
                    self.device.set_stay_awake(True)
                self.q.put(("dev", (True, model)))
            elif not ok and self.connected is not False:
                self.q.put(("dev", (False, None)))
            time.sleep(3)

    def on_device(self, ok, model):
        self.connected = ok
        if ok:
            self.model = model
            self.status.config(text=t("connected", model=model), foreground="#1a7f37")
            cache = self.cfg.get("cameras_cache") or {}
            if not self.cameras or cache.get("model") != model:
                self.detect_cameras()
        else:
            self.status.config(text=t("disconnected"), foreground="#999999")

    def poll(self):
        try:
            while True:
                kind, val = self.q.get_nowait()
                if kind == "log":
                    self.logbox.config(state="normal")
                    self.logbox.insert("end", val + "\n")
                    self.logbox.see("end")
                    self.logbox.config(state="disabled")
                elif kind == "dev":
                    self.on_device(*val)
                elif kind == "cams":
                    self.on_cameras(*val)
                elif kind == "ended":
                    self.on_ended(val)
        except queue.Empty:
            pass
        if self.rec_start:
            s = int(time.time() - self.rec_start)
            self.rec_lbl.config(text=t("recording", t=f"{s // 60:02d}:{s % 60:02d}"))
        self.root.after(200, self.poll)

    # ---------------- Virtual camera ----------------
    def camera_hwnd(self):
        proc = self.proc
        if self.mode not in ("preview", "record") or proc is None or proc.poll() is not None:
            return None
        hw = winapi.windows_of(proc.pid)
        return hw[0] if hw else None

    def toggle_vcam(self):
        if not self.vcam_on.get():
            if self.vcam:
                self.vcam.stop()
                self.vcam = None
                self.log(t("vcam_off"))
            return
        try:
            vc = VirtualCam(self.camera_hwnd, self.log)
        except ImportError as e:
            self.vcam_on.set(False)
            # Install into THE SAME Python that runs this app (there may be several installed)
            exe = sys.executable
            if os.path.basename(exe).lower() == "pythonw.exe":
                exe = os.path.join(os.path.dirname(exe), "python.exe")
            cmd = f'& "{exe}" -m pip install {PIP_PACKAGES}'
            self.root.clipboard_clear()
            self.root.clipboard_append(cmd)
            messagebox.showinfo(APP_NAME, t("missing_lib", err=e, cmd=cmd))
            return
        try:
            vc.start()
        except Exception as e:
            self.vcam_on.set(False)
            messagebox.showerror(APP_NAME, t("vcam_open_error", err=e))
            return
        self.vcam = vc
        self.log(t("vcam_on"))
        if not self.busy:
            self.preview()

    def on_close(self):
        if self.running():
            if not messagebox.askyesno(APP_NAME, t("confirm_quit")):
                return
            self.restart_pending = self.pending_record = False
            self.stop()
            for _ in range(50):
                if not self.running():
                    break
                time.sleep(0.1)
        if self.vcam:
            self.vcam.stop()
        self.save_cfg()
        self.root.destroy()


class SettingsDialog:
    def __init__(self, app):
        self.app = app
        cfg = app.cfg
        top = self.top = tk.Toplevel(app.root)
        top.title(t("settings"))
        top.resizable(False, False)
        top.transient(app.root)
        top.grab_set()

        self.lang_codes = ["auto"] + list(LANGS)
        self.lang_names = [t("lang_auto")] + list(LANGS.values())
        self.lang = tk.StringVar(value=self.lang_names[self.lang_codes.index(cfg["language"])]
                                 if cfg["language"] in self.lang_codes else self.lang_names[0])
        self.pin = tk.StringVar(value=app.pin())
        self.show_pin = tk.BooleanVar(value=False)
        self.auto_unlock = tk.BooleanVar(value=cfg["auto_unlock"])
        self.stay_awake = tk.BooleanVar(value=cfg["stay_awake"])
        self.adb_path = tk.StringVar(value=cfg["adb_path"])
        self.scrcpy_path = tk.StringVar(value=cfg["scrcpy_path"])
        self.outdir = tk.StringVar(value=cfg["outdir"])

        f = ttk.Frame(top, padding=12)
        f.grid()

        lf = ttk.Frame(f)
        lf.grid(row=0, column=0, sticky="w", pady=(0, 6))
        ttk.Label(lf, text=t("language")).pack(side="left")
        ttk.Combobox(lf, textvariable=self.lang, values=self.lang_names, width=14,
                     state="readonly").pack(side="left", padx=6)

        lk = ttk.LabelFrame(f, text=t("lock_section"), padding=8)
        lk.grid(row=1, column=0, sticky="we", pady=4)
        ttk.Label(lk, text=t("pin")).grid(row=0, column=0, sticky="w")
        self.pin_entry = ttk.Entry(lk, textvariable=self.pin, show="•", width=22)
        self.pin_entry.grid(row=0, column=1, sticky="w", padx=6)
        ttk.Checkbutton(lk, text=t("show"), variable=self.show_pin, command=self.toggle_show).grid(
            row=0, column=2, sticky="w")
        ttk.Checkbutton(lk, text=t("auto_unlock"), variable=self.auto_unlock).grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(6, 0))
        ttk.Checkbutton(lk, text=t("stay_awake"), variable=self.stay_awake).grid(
            row=2, column=0, columnspan=3, sticky="w")
        ttk.Label(lk, text=t("pin_note"), foreground="#777777", font=("Segoe UI", 8)).grid(
            row=3, column=0, columnspan=3, sticky="w", pady=(6, 0))
        ttk.Button(lk, text=t("test_unlock"), command=self.test_unlock).grid(
            row=4, column=0, columnspan=3, sticky="w", pady=(6, 0))

        pf = ttk.LabelFrame(f, text=t("paths"), padding=8)
        pf.grid(row=2, column=0, sticky="we", pady=4)
        rows = (("adb", self.adb_path, False), ("scrcpy", self.scrcpy_path, False), (t("outdir"), self.outdir, True))
        for i, (label, var, is_dir) in enumerate(rows):
            ttk.Label(pf, text=label).grid(row=i, column=0, sticky="w")
            ttk.Entry(pf, textvariable=var, width=42).grid(row=i, column=1, sticky="w", padx=6, pady=1)
            ttk.Button(pf, text="…", width=3, command=lambda v=var, d=is_dir: self.browse(v, d)).grid(
                row=i, column=2)
        ttk.Label(pf, text=t("auto_hint"), foreground="#777777", font=("Segoe UI", 8)).grid(
            row=3, column=1, sticky="w", padx=6)

        bf = ttk.Frame(f)
        bf.grid(row=3, column=0, sticky="e", pady=(8, 0))
        ttk.Button(bf, text=t("cancel"), command=top.destroy).pack(side="right", padx=2)
        ttk.Button(bf, text=t("save"), command=self.save).pack(side="right", padx=2)

        self.pin_entry.focus_set()

    def toggle_show(self):
        self.pin_entry.config(show="" if self.show_pin.get() else "•")

    def browse(self, var, is_dir):
        if is_dir:
            path = filedialog.askdirectory(parent=self.top, initialdir=var.get() or None)
        else:
            path = filedialog.askopenfilename(parent=self.top, filetypes=[("exe", "*.exe"), ("*", "*.*")])
        if path:
            var.set(os.path.normpath(path))

    def test_unlock(self):
        app, pin = self.app, self.pin.get()
        if not app.connected:
            messagebox.showwarning(APP_NAME, t("no_device"), parent=self.top)
            return

        def work():
            result = app.device.unlock(pin)
            app.log(t({"unlocked": "unlocked", "already": "already_unlocked",
                       "failed": "still_locked", "no_pin": "no_pin"}[result]))
        threading.Thread(target=work, daemon=True).start()

    def save(self):
        app, cfg = self.app, self.app.cfg
        new_lang = self.lang_codes[self.lang_names.index(self.lang.get())]
        lang_changed = new_lang != cfg["language"]
        cfg.update({
            "language": new_lang,
            "pin_enc": config.protect(self.pin.get()),
            "auto_unlock": self.auto_unlock.get(),
            "stay_awake": self.stay_awake.get(),
            "adb_path": self.adb_path.get().strip(),
            "scrcpy_path": self.scrcpy_path.get().strip(),
            "outdir": self.outdir.get().strip() or config.DEFAULTS["outdir"],
        })
        config.save(cfg)
        app.no_pin_warned = False
        app.resolve_tools()
        if app.connected:
            threading.Thread(target=app.device.set_stay_awake, args=(cfg["stay_awake"],), daemon=True).start()
        self.top.destroy()
        if lang_changed:
            messagebox.showinfo(APP_NAME, t("restart_lang"))


def main():
    root = tk.Tk()

    def report(exc, val, tb):  # errors inside buttons/timers would otherwise be invisible in a .pyw
        import traceback
        messagebox.showerror(APP_NAME, "".join(traceback.format_exception(exc, val, tb))[-1500:])
    root.report_callback_exception = report
    try:
        ttk.Style().theme_use("vista")
    except Exception:
        pass
    App(root)
    root.mainloop()
