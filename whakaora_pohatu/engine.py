"""
Whakaora Pōhatu — core game engine
====================================
Stone Story RPG soul, te ao Māori kawa, dual-memory mesh.

Local memory  : ~/.whakaora/local_save.json      (your choices, your whakapapa)
Nonlocal memory: ~/.whakaora/nonlocal_mesh.json  (collective mana pulse, simulated)
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

# ── paths ──────────────────────────────────────────────────────────────────────
SAVE_DIR = Path.home() / ".whakaora"
LOCAL_PATH    = SAVE_DIR / "local_save.json"
NONLOCAL_PATH = SAVE_DIR / "nonlocal_mesh.json"

SAVE_DIR.mkdir(exist_ok=True)

# ── constants ──────────────────────────────────────────────────────────────────
MARAMATAKA_PHASES = [
    "Whiro",        # dark moon — danger peaks
    "Tirea",        # first light — risk moderate
    "Hoata",        # glimmering — balanced
    "Ōuenuku",      # growing light — restorative favoured
    "Okoro",        # waxing — mana regenerates
    "Tamatea",      # storm — tapu heightened
    "Ōtāne",        # planting — kawakawa thrives
    "Ōrongonui",    # abundance — nonlocal sync stronger
    "Māuri",        # life force — full power
    "Ōturu",        # full moon — maximum mana
    "Rākaunui",     # peak strength
    "Rākaumatohi",  # consolidation
    "Takirau",      # waning — utu risk rises
    "Ōike",         # receding
    "Korekore",     # void — Te Kore pulses
    "Tangaroa",     # deep sea — taniwha active
    "Ōtāne-hou",   # renewal seed
    "Māuri-hou",    # life reseeding
    "Mutuwhenua",   # earth silence
    "Whiro-hou",    # returning dark
]

TANIWHA_MOODS = ["dormant", "curious", "wary", "hostile", "appeased"]

KAWAKAWA_ZONES = [
    "Awa Tapu",
    "Maunga Kura",
    "Repo Ora",
    "Waoku Atua",
    "Tai Pari",
]

MATARIKI_STARS = [
    "Matariki",   # overall wellbeing
    "Pōhutukawa", # the dead
    "Tupuānuku",  # food from the ground
    "Tupuārangi", # food from above
    "Waitī",      # fresh water
    "Waitā",      # salt water
    "Waipuna-ā-Rangi", # rain
    "Ururangi",   # winds
    "Hiwa-i-te-rangi",  # wishing star
]


# ── L-system koru ──────────────────────────────────────────────────────────────

def lsystem(axiom: str, rules: dict[str, str], iterations: int) -> str:
    s = axiom
    for _ in range(iterations):
        s = "".join(rules.get(c, c) for c in s)
    return s


def koru_to_ascii(lstr: str, mana_pct: float, chaos: bool) -> list[str]:
    """
    Turtle-graphics-style conversion of an L-string to ASCII lines.
    Uses a 2-D integer grid; returns a list of strings (the canvas rows).
    """
    W, H = 40, 20
    canvas = [[" "] * W for _ in range(H)]

    x, y = W // 2, H - 2
    angle = 90.0          # degrees, 0 = right
    stack: list[tuple[float, float, float]] = []

    # Character set shifts with mana/chaos
    if chaos:
        draw_chars = list("!@#%^&*><\\|/~")
    else:
        intensity = mana_pct
        if intensity > 0.75:
            draw_chars = ["*", "o", ".", "·", "+"]
        elif intensity > 0.4:
            draw_chars = ["o", ".", "-", "+", "~"]
        else:
            draw_chars = [".", ",", "`", "·", " "]

    def put(px: int, py: int) -> None:
        if 0 <= px < W and 0 <= py < H:
            canvas[py][px] = random.choice(draw_chars)

    for ch in lstr:
        if ch == "F":
            rad = math.radians(angle)
            nx = x + round(math.cos(rad) * 1.5)
            ny = y - round(math.sin(rad))
            put(int(x), int(y))
            x, y = nx, ny
        elif ch == "+":
            angle += 25.7
        elif ch == "-":
            angle -= 25.7
        elif ch == "[":
            stack.append((x, y, angle))
        elif ch == "]":
            if stack:
                x, y, angle = stack.pop()
        # X, A etc. are structural — no movement

    put(int(x), int(y))
    return ["".join(row) for row in canvas]


def build_koru(mana_pct: float, chaos: bool, depth: int = 4) -> list[str]:
    """Generate a koru fractal at the given mana level."""
    rules = {
        "X": "F+[[X]-X]-F[-FX]+X",
        "F": "FF",
    }
    ls = lsystem("X", rules, min(depth, 5))
    return koru_to_ascii(ls, mana_pct, chaos)


# ── mana bar ───────────────────────────────────────────────────────────────────

def mana_bar(mana: float, width: int = 20) -> str:
    filled = round(mana * width)
    empty  = width - filled
    return "█" * filled + "░" * empty


# ── memory layer ───────────────────────────────────────────────────────────────

def _load_json(path: Path, default: dict) -> dict:
    try:
        if path.exists():
            return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        pass
    return dict(default)


def _save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def merkle_hash(data: dict) -> str:
    blob = json.dumps(data, sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(blob).hexdigest()[:16]


# ── game state ────────────────────────────────────────────────────────────────

@dataclass
class LocalMemory:
    """Personal save — the kaitiaki's own whakapapa of choices."""
    karakia_used: list[str]       = field(default_factory=list)
    kawakawa_planted: list[str]   = field(default_factory=list)
    matariki_reunited: list[str]  = field(default_factory=list)
    utu_events: int               = 0
    ora_events: int               = 0
    last_moon: str                = "Hoata"
    merkle: str                   = ""

    def save(self) -> None:
        d = asdict(self)
        d["merkle"] = merkle_hash(d)
        _save_json(LOCAL_PATH, d)

    @classmethod
    def load(cls) -> "LocalMemory":
        d = _load_json(LOCAL_PATH, {})
        obj = cls(
            karakia_used      = d.get("karakia_used", []),
            kawakawa_planted  = d.get("kawakawa_planted", []),
            matariki_reunited = d.get("matariki_reunited", []),
            utu_events        = d.get("utu_events", 0),
            ora_events        = d.get("ora_events", 0),
            last_moon         = d.get("last_moon", "Hoata"),
            merkle            = d.get("merkle", ""),
        )
        return obj


@dataclass
class NonlocalMesh:
    """
    Collective-memory layer — simulates a community blockchain pulse.
    In a real deployment this would sync with peers; here we mock it
    with a local file that persists across sessions as a proxy for
    'shared whenua memory'.
    """
    community_mana: float          = 0.5
    matariki_aligned: list[str]    = field(default_factory=list)
    corruption_level: float        = 0.0
    kawakawa_total: int            = 0
    sync_hash: str                 = ""
    last_sync: str                 = ""

    def pulse(self, ora_delta: float, utu_delta: float) -> None:
        """Apply a local action's ripple to the collective."""
        self.community_mana = max(0.0, min(1.0,
            self.community_mana + ora_delta * 0.05 - utu_delta * 0.08))
        self.corruption_level = max(0.0, min(1.0,
            self.corruption_level + utu_delta * 0.06 - ora_delta * 0.03))

    def save(self) -> None:
        d = asdict(self)
        d["sync_hash"] = merkle_hash(d)
        d["last_sync"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        _save_json(NONLOCAL_PATH, d)

    @classmethod
    def load(cls) -> "NonlocalMesh":
        d = _load_json(NONLOCAL_PATH, {})
        return cls(
            community_mana    = d.get("community_mana", 0.5),
            matariki_aligned  = d.get("matariki_aligned", []),
            corruption_level  = d.get("corruption_level", 0.0),
            kawakawa_total    = d.get("kawakawa_total", 0),
            sync_hash         = d.get("sync_hash", ""),
            last_sync         = d.get("last_sync", ""),
        )


@dataclass
class PohaturState:
    """The Thaumiel pōhatu — restorative or chaotic, never neutral for long."""
    mode: str        = "restorative"   # "restorative" | "chaotic"
    mana: float      = 0.72
    tapu_charge: float = 0.0           # builds on reckless utu; triggers void event

    def toggle(self, to: str) -> None:
        assert to in ("restorative", "chaotic")
        self.mode = to

    @property
    def glyph(self) -> str:
        if self.mode == "restorative":
            return "🌿" if self.mana > 0.5 else "~"
        return "🔥" if self.tapu_charge < 0.6 else "☠"
