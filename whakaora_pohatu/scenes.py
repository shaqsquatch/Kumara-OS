"""
Whakaora Pōhatu — scene definitions
=====================================
Each scene is a dataclass with a `render()` method that returns a list of
display lines, plus `choices()` returning available karakia/actions.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .engine import LocalMemory, NonlocalMesh, PohaturState

from .engine import (
    KAWAKAWA_ZONES,
    MATARIKI_STARS,
    MARAMATAKA_PHASES,
    TANIWHA_MOODS,
    build_koru,
    mana_bar,
)


def _divider(char: str = "─", width: int = 52) -> str:
    return char * width


def _header(title: str, pohatu: "PohaturState") -> list[str]:
    lines = [
        _divider("═"),
        f"  {title}",
        _divider("─"),
        f"  Mana:    [{mana_bar(pohatu.mana)}]  {round(pohatu.mana*100):>3}%",
        f"  Pōhatu:  {pohatu.mode.capitalize():12s}  {pohatu.glyph}",
        f"  Tapu:    [{mana_bar(pohatu.tapu_charge, 10)}]",
        _divider("─"),
    ]
    return lines


# ── Scene 1 — Te Ao Pō entry ──────────────────────────────────────────────────

@dataclass
class KoruGroveScene:
    moon_phase: str

    def render(self, pohatu: "PohaturState",
               local: "LocalMemory", mesh: "NonlocalMesh") -> list[str]:
        chaos = pohatu.mode == "chaotic"
        koru  = build_koru(pohatu.mana, chaos, depth=4)

        lines: list[str] = []
        lines += _header("Te Ao Pō — Fractal Koru Grove", pohatu)
        lines.append(f"  Maramataka: {self.moon_phase}")
        lines.append(f"  Community mana mesh: {round(mesh.community_mana*100):>3}%  "
                     f"| Corruption: {round(mesh.corruption_level*100):>3}%")
        lines.append(_divider("─"))
        lines += ["  " + row for row in koru]
        lines.append(_divider("─"))

        # contextual flavour
        if chaos:
            lines.append("  The koru unravels — chaos-light bleeds into the branches.")
        elif pohatu.mana > 0.7:
            lines.append("  The koru breathes. Mana hums through root and stone.")
        else:
            lines.append("  The koru flickers. The grove is dimming.")

        if pohatu.tapu_charge > 0.5:
            lines.append("  ⚠  A tapu breach resonates — Te Kore stirs in the void.")

        # nonlocal community pulse
        if mesh.community_mana > 0.7:
            lines.append("  ✦  Nonlocal pulse: distant kaitiaki add their mana.")
        elif mesh.corruption_level > 0.5:
            lines.append("  ✦  Nonlocal pulse: the mesh is corrupted — others struggle.")

        # personal whakapapa
        if local.kawakawa_planted:
            zones = ", ".join(local.kawakawa_planted[-3:])
            lines.append(f"  Your kawakawa grows in: {zones}.")
        if local.matariki_reunited:
            stars = ", ".join(local.matariki_reunited[-3:])
            lines.append(f"  Stars you have called home: {stars}.")

        lines.append(_divider("═"))
        return lines

    def choices(self, pohatu: "PohaturState",
                local: "LocalMemory", mesh: "NonlocalMesh") -> list[tuple[str, str]]:
        opts = [
            ("whakapapa ora",  "Speak restoration — heal the grove (+mana, +ora)"),
            ("wero chaos",     "Invoke utu — shatter the silence (+tapu, +entropy)"),
            ("tiaki kawakawa", "Plant kawakawa in a tapu zone (uses 0.10 mana)"),
            ("karakia matariki","Call a Matariki star back to the sky"),
            ("korero taniwha", "Negotiate with the stirring taniwha"),
            ("tatari",         "Wait and listen (skip — let the maramataka turn)"),
        ]
        if mesh.community_mana > 0.6 and not pohatu.mode == "chaotic":
            opts.insert(0, ("tūhono kāpua",
                            "Sync with the nonlocal mesh — share mana pulse"))
        return opts


# ── Scene 2 — Taniwha Parley ──────────────────────────────────────────────────

@dataclass
class TaniwhaScene:
    mood: str = "curious"

    def render(self, pohatu: "PohaturState",
               local: "LocalMemory", mesh: "NonlocalMesh") -> list[str]:
        lines = _header("Te Awa Taniwha — Negotiation", pohatu)
        lines.append(f"  Taniwha mood: {self.mood.upper()}")
        lines.append(_divider("─"))
        lines += self._ascii_taniwha(self.mood, pohatu.mode == "chaotic")
        lines.append(_divider("─"))
        if self.mood == "hostile":
            lines.append("  The taniwha's scales catch the last light.  DANGER.")
        elif self.mood == "appeased":
            lines.append("  It lowers its head. A ripple of warmth crosses the awa.")
        elif self.mood == "dormant":
            lines.append("  Deep bubbles. It knows you are here.")
        else:
            lines.append("  It watches. Your next word matters.")

        if local.utu_events > 2:
            lines.append("  Your reputation for utu precedes you — it is wary.")
        if local.ora_events > 3:
            lines.append("  It senses your restorative history. Trust is possible.")
        lines.append(_divider("═"))
        return lines

    @staticmethod
    def _ascii_taniwha(mood: str, chaos: bool) -> list[str]:
        if mood == "hostile":
            return [
                "       /\\___/\\  ~~~",
                "      ( >   < )  <<< TEETH",
                "       \\  ^  /",
                "    ~~~~`-.-'~~~~ awa",
            ]
        elif mood == "appeased":
            return [
                "       /~___~\\",
                "      ( -   - )",
                "       \\  u  /",
                "    ~~~~`---'~~~~ awa",
            ]
        else:
            fill = "?" if chaos else "o"
            return [
                f"       /_{fill}___{fill}_\\",
                "      ( ?   ? )",
                "       \\  ~  /",
                "    ~~~~`---'~~~~ awa",
            ]

    def choices(self, pohatu: "PohaturState",
                local: "LocalMemory", mesh: "NonlocalMesh") -> list[tuple[str, str]]:
        opts = [
            ("karakia awa",  "Offer a water karakia — gentle approach"),
            ("homai taonga", "Offer a taonga — costs 0.15 mana, may appease"),
            ("wero",         "Challenge directly — high risk, tests utu charge"),
            ("hoki atu",     "Retreat to the grove"),
        ]
        if local.ora_events > 2:
            opts.insert(0, ("whakapapa korero",
                            "Share your restorative lineage — trust bonus"))
        return opts


# ── Scene 3 — Matariki Ritual ─────────────────────────────────────────────────

@dataclass
class MatarikiScene:
    stars_remaining: list[str]

    def render(self, pohatu: "PohaturState",
               local: "LocalMemory", mesh: "NonlocalMesh") -> list[str]:
        lines = _header("Te Iwa Kāhui o Matariki", pohatu)
        lines.append(_divider("─"))
        lines += self._sky(pohatu.mana, local.matariki_reunited)
        lines.append(_divider("─"))
        aligned = mesh.matariki_aligned
        lines.append(f"  Stars reunited: {len(local.matariki_reunited)}/9")
        if aligned:
            lines.append(f"  Nonlocal consensus on: {', '.join(aligned[:3])}")
        lines.append(_divider("═"))
        return lines

    @staticmethod
    def _sky(mana: float, reunited: list[str]) -> list[str]:
        all_stars = MATARIKI_STARS
        rows = [""]
        row: list[str] = []
        for i, s in enumerate(all_stars):
            if s in reunited:
                glyph = "★"
            elif mana > 0.6:
                glyph = "✦"
            else:
                glyph = "·"
            row.append(f"{glyph} {s:<22}")
            if len(row) == 3:
                rows.append("  " + "  ".join(row))
                row = []
        if row:
            rows.append("  " + "  ".join(row))
        rows.append("")
        return rows

    def choices(self, pohatu: "PohaturState",
                local: "LocalMemory", mesh: "NonlocalMesh") -> list[tuple[str, str]]:
        opts = []
        for star in self.stars_remaining[:4]:
            opts.append((f"karakia {star.lower()}",
                         f"Call {star} home (costs 0.12 mana)"))
        opts.append(("hoki atu", "Return to the grove"))
        return opts
