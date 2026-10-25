"""Reading the phone's cameras from `scrcpy --list-cameras`."""
import re
import subprocess
from dataclasses import dataclass, field

from .device import NOWIN

# Example line (scrcpy 5):
#   --camera-id=0    (back, 4080x3072, fps={15, 24, 30, 60}, zoom-range=[0.49, 30])
_LINE = re.compile(
    r"--camera-id=(?P<id>\S+)\s+\((?P<facing>[\w-]+),\s*(?P<w>\d+)x(?P<h>\d+)"
    r"(?:,\s*fps=[\[{](?P<fps>[^\]}]*)[\]}])?"
    r"(?:,\s*zoom-range=\[(?P<zmin>[\d.]+),\s*(?P<zmax>[\d.]+)\])?"
)


@dataclass
class Camera:
    id: str
    facing: str
    width: int
    height: int
    fps: list = field(default_factory=list)
    zoom: tuple = None  # (min, max) or None

    def label(self):
        return f"{self.id} · {self.facing.capitalize()} · {self.width}×{self.height}"

    def to_dict(self):
        return {"id": self.id, "facing": self.facing, "width": self.width, "height": self.height,
                "fps": self.fps, "zoom": list(self.zoom) if self.zoom else None}

    @classmethod
    def from_dict(cls, d):
        return cls(d["id"], d["facing"], d["width"], d["height"], d.get("fps") or [],
                   tuple(d["zoom"]) if d.get("zoom") else None)


def parse_cameras(text):
    cams = []
    for line in text.splitlines():
        m = _LINE.search(line)
        if not m:
            continue
        fps = [int(x) for x in re.findall(r"\d+", m.group("fps") or "")]
        zoom = (float(m.group("zmin")), float(m.group("zmax"))) if m.group("zmin") else None
        cams.append(Camera(m.group("id"), m.group("facing"), int(m.group("w")), int(m.group("h")),
                           sorted(set(fps)), zoom))
    return cams


def list_cameras(scrcpy_path, env, timeout=30):
    """Returns (cameras, raw_output)."""
    try:
        r = subprocess.run([scrcpy_path, "-d", "--list-cameras"], capture_output=True, text=True,
                           timeout=timeout, env=env, creationflags=NOWIN, errors="replace")
        out = (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return [], str(e)
    return parse_cameras(out), out


def zoom_presets(zoom_range):
    """Quick zoom buttons that fit the camera's range, e.g. (0.49, 30) -> [0.49, 1, 2, 5, 10]."""
    if not zoom_range:
        return []
    zmin, zmax = zoom_range
    presets = [zmin] if zmin < 1 else []
    presets += [z for z in (1, 2, 5, 10) if zmin <= z <= zmax]
    return presets


def default_fps(fps_list, wanted=30):
    if not fps_list:
        return str(wanted)
    if wanted in fps_list:
        return str(wanted)
    lower = [f for f in fps_list if f <= wanted]
    return str(max(lower) if lower else min(fps_list))
