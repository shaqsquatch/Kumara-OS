"""
Whakaora Pōhatu — main game loop
==================================
Auto-plays the pōhatu's journey; player chooses karakia at each beat.
Pure stdlib — no third-party dependencies.
"""

from __future__ import annotations

import os
import random
import time
from typing import Optional

from .engine import (
    KAWAKAWA_ZONES,
    MARAMATAKA_PHASES,
    MATARIKI_STARS,
    TANIWHA_MOODS,
    LocalMemory,
    NonlocalMesh,
    PohaturState,
)
from .scenes import KoruGroveScene, MatarikiScene, TaniwhaScene


# ── terminal helpers ───────────────────────────────────────────────────────────

def clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def typewrite(text: str, delay: float = 0.018) -> None:
    for ch in text:
        print(ch, end="", flush=True)
        time.sleep(delay)
    print()


def print_lines(lines: list[str], delay: float = 0.004) -> None:
    for line in lines:
        print(line)
        time.sleep(delay)


def prompt_choice(choices: list[tuple[str, str]]) -> str:
    print()
    for i, (cmd, desc) in enumerate(choices, 1):
        print(f"  [{i}] {cmd:<22}  — {desc}")
    print()
    while True:
        raw = input("  Your karakia › ").strip().lower()
        # accept number shortcut
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(choices):
                return choices[idx][0]
        # accept partial text match
        for cmd, _ in choices:
            if raw in cmd.lower() or cmd.lower().startswith(raw):
                return cmd
        print("  (Ehara — try again, or type the number)")


# ── action resolvers ──────────────────────────────────────────────────────────

def resolve_grove(
    action: str,
    pohatu: PohaturState,
    local: LocalMemory,
    mesh: NonlocalMesh,
    moon: str,
) -> str:
    """Apply a grove-scene action; returns a narrative line."""

    if action == "whakapapa ora":
        gain = random.uniform(0.06, 0.14)
        pohatu.mana = min(1.0, pohatu.mana + gain)
        pohatu.tapu_charge = max(0.0, pohatu.tapu_charge - 0.05)
        pohatu.toggle("restorative")
        local.ora_events += 1
        mesh.pulse(ora_delta=1.0, utu_delta=0.0)
        local.karakia_used.append("whakapapa ora")
        return f"  Mana flows +{round(gain*100)}%. The koru unfurls. Restorative mode set."

    elif action == "wero chaos":
        cost = random.uniform(0.05, 0.12)
        pohatu.mana = max(0.0, pohatu.mana - cost)
        pohatu.tapu_charge = min(1.0, pohatu.tapu_charge + 0.18)
        pohatu.toggle("chaotic")
        local.utu_events += 1
        mesh.pulse(ora_delta=0.0, utu_delta=1.0)
        local.karakia_used.append("wero chaos")
        msg = f"  Utu released. Mana -{round(cost*100)}%. Tapu charge rises."
        if pohatu.tapu_charge > 0.8:
            msg += "\n  ⚠  TAPU CRITICAL — Te Kore breach imminent!"
        return msg

    elif action == "tiaki kawakawa":
        if pohatu.mana < 0.10:
            return "  Not enough mana to plant. Rest first."
        pohatu.mana -= 0.10
        zone = random.choice([z for z in KAWAKAWA_ZONES
                               if z not in local.kawakawa_planted] or KAWAKAWA_ZONES)
        local.kawakawa_planted.append(zone)
        mesh.kawakawa_total += 1
        mesh.pulse(ora_delta=0.8, utu_delta=0.0)
        return f"  Kawakawa planted in {zone}. The whenua remembers."

    elif action == "karakia matariki":
        return "navigate:matariki"

    elif action == "korero taniwha":
        return "navigate:taniwha"

    elif action == "tūhono kāpua":
        shared = mesh.community_mana
        pohatu.mana = min(1.0, pohatu.mana + shared * 0.1)
        return (f"  Nonlocal sync: community mana ({round(shared*100)}%) "
                f"adds +{round(shared*10)}% to your pōhatu.")

    elif action == "tatari":
        drift = random.uniform(-0.03, 0.05)
        pohatu.mana = max(0.0, min(1.0, pohatu.mana + drift))
        return ("  You wait. The maramataka turns. "
                f"Mana shifts {'+' if drift>=0 else ''}{round(drift*100)}%.")

    return "  ..."


def resolve_taniwha(
    action: str,
    pohatu: PohaturState,
    local: LocalMemory,
    mesh: NonlocalMesh,
    scene: TaniwhaScene,
) -> str:
    if action == "hoki atu":
        return "navigate:grove"

    if action == "karakia awa":
        if scene.mood in ("curious", "wary", "dormant"):
            scene.mood = "appeased"
            pohatu.mana = min(1.0, pohatu.mana + 0.08)
            local.ora_events += 1
            mesh.pulse(ora_delta=0.7, utu_delta=0.0)
            return "  The water karakia soothes. The taniwha quietens."
        return "  The taniwha ignores the karakia. Its mood is fixed."

    if action == "homai taonga":
        if pohatu.mana < 0.15:
            return "  Not enough mana to offer a taonga."
        pohatu.mana -= 0.15
        if scene.mood != "hostile":
            scene.mood = "appeased"
            local.ora_events += 1
            return "  Taonga offered. The taniwha bows its great head."
        return "  The taonga dissolves in the current. Hostile moods run deep."

    if action == "wero":
        pohatu.tapu_charge = min(1.0, pohatu.tapu_charge + 0.25)
        local.utu_events += 1
        mesh.pulse(ora_delta=0.0, utu_delta=1.5)
        if scene.mood in ("curious", "dormant"):
            scene.mood = "hostile"
            return "  The challenge wakes its fury. HOSTILE."
        elif scene.mood == "wary":
            scene.mood = "hostile"
            return "  It takes the wero — and answers with teeth."
        return "  You already face its full wrath. The tapu charge peaks."

    if action == "whakapapa korero":
        scene.mood = "appeased"
        local.ora_events += 2
        mesh.pulse(ora_delta=1.2, utu_delta=0.0)
        return "  Your lineage of restoration speaks. Deep recognition passes between you."

    return "  The taniwha watches without response."


def resolve_matariki(
    action: str,
    pohatu: PohaturState,
    local: LocalMemory,
    mesh: NonlocalMesh,
) -> str:
    if action == "hoki atu":
        return "navigate:grove"

    # action like "karakia hiwa-i-te-rangi"
    parts = action.split(" ", 1)
    if len(parts) == 2 and parts[0] == "karakia":
        star_fragment = parts[1].strip()
        # fuzzy match
        matched = next(
            (s for s in MATARIKI_STARS
             if star_fragment.lower() in s.lower()
             or s.lower().startswith(star_fragment.lower())),
            None,
        )
        if not matched:
            return f"  No star answers to '{star_fragment}'."
        if matched in local.matariki_reunited:
            return f"  {matched} is already home."
        if pohatu.mana < 0.12:
            return "  Not enough mana to call a star."
        pohatu.mana -= 0.12
        local.matariki_reunited.append(matched)
        mesh.matariki_aligned.append(matched)
        mesh.pulse(ora_delta=1.0, utu_delta=0.0)
        msg = f"  {matched} rises — a ribbon of light crosses Te Ao Pō."
        if len(local.matariki_reunited) == 9:
            msg += "\n  ✦✦✦  All nine stars home. Matariki is complete. ✦✦✦"
        return msg

    return "  The karakia drifts upward, unanswered."


# ── Te Kore void event ─────────────────────────────────────────────────────────

def te_kore_event(pohatu: PohaturState, local: LocalMemory, mesh: NonlocalMesh) -> None:
    """Fires when tapu_charge > 0.8 — a generative-void interruption."""
    clear()
    typewrite("\n  ░░░░  TE KORE  ░░░░", 0.03)
    typewrite("  The fractal collapses. Void pulses through the mesh.", 0.02)
    time.sleep(0.8)
    typewrite("  Patterns unmake themselves...", 0.02)
    time.sleep(0.6)
    # partial reset — the void 'reseeds' chaos into new growth
    pohatu.tapu_charge = 0.0
    pohatu.mana = max(0.15, pohatu.mana - 0.20)
    pohatu.toggle("restorative")
    mesh.corruption_level = min(1.0, mesh.corruption_level + 0.15)
    local.utu_events += 1
    typewrite(f"  Pōhatu reseeds. Mana: {round(pohatu.mana*100)}%.  Mode: restorative.", 0.02)
    typewrite("  The void has spoken. You continue.", 0.02)
    time.sleep(1.0)


# ── maramataka clock ──────────────────────────────────────────────────────────

def advance_moon(local: LocalMemory) -> str:
    idx = MARAMATAKA_PHASES.index(local.last_moon) if local.last_moon in MARAMATAKA_PHASES else 0
    idx = (idx + 1) % len(MARAMATAKA_PHASES)
    local.last_moon = MARAMATAKA_PHASES[idx]
    return local.last_moon


# ── main loop ─────────────────────────────────────────────────────────────────

def run(max_turns: int = 0) -> None:
    """
    Run the game. max_turns=0 means run until the player quits or wins.
    Set max_turns > 0 for scripted demo / testing.
    """
    local  = LocalMemory.load()
    mesh   = NonlocalMesh.load()
    pohatu = PohaturState()

    # Initialise taniwha with moon-influenced mood
    moon_idx     = MARAMATAKA_PHASES.index(local.last_moon) if local.last_moon in MARAMATAKA_PHASES else 2
    taniwha_mood = TANIWHA_MOODS[moon_idx % len(TANIWHA_MOODS)]
    taniwha_scene = TaniwhaScene(mood=taniwha_mood)

    stars_left = [s for s in MATARIKI_STARS if s not in local.matariki_reunited]
    matariki_scene = MatarikiScene(stars_remaining=stars_left)

    current = "grove"
    turn    = 0

    clear()
    typewrite("\n  Nau mai, haere mai, kaitiaki.", 0.025)
    typewrite("  Te Ao Pō awaits. The pōhatu pulses in your hands.", 0.02)
    time.sleep(0.6)

    while True:
        if max_turns and turn >= max_turns:
            break

        # ── te kore interrupt ──
        if pohatu.tapu_charge > 0.8:
            te_kore_event(pohatu, local, mesh)
            stars_left = [s for s in MATARIKI_STARS if s not in local.matariki_reunited]
            matariki_scene = MatarikiScene(stars_remaining=stars_left)

        # ── victory check ──
        if len(local.matariki_reunited) == 9:
            _victory(pohatu, local, mesh)
            break

        # ── render ──
        clear()
        moon = local.last_moon

        if current == "grove":
            grove = KoruGroveScene(moon_phase=moon)
            print_lines(grove.render(pohatu, local, mesh))
            choices = grove.choices(pohatu, local, mesh)

        elif current == "taniwha":
            print_lines(taniwha_scene.render(pohatu, local, mesh))
            choices = taniwha_scene.choices(pohatu, local, mesh)

        elif current == "matariki":
            stars_left = [s for s in MATARIKI_STARS if s not in local.matariki_reunited]
            matariki_scene = MatarikiScene(stars_remaining=stars_left)
            print_lines(matariki_scene.render(pohatu, local, mesh))
            choices = matariki_scene.choices(pohatu, local, mesh)

        else:
            current = "grove"
            continue

        # ── player input ──
        action = prompt_choice(choices)
        print()

        # ── resolve ──
        if current == "grove":
            result = resolve_grove(action, pohatu, local, mesh, moon)
        elif current == "taniwha":
            result = resolve_taniwha(action, pohatu, local, mesh, taniwha_scene)
        elif current == "matariki":
            result = resolve_matariki(action, pohatu, local, mesh)
        else:
            result = ""

        # navigation tokens
        if result.startswith("navigate:"):
            current = result.split(":", 1)[1]
        else:
            typewrite(result, 0.015)
            time.sleep(0.4)

        # ── passive mana drift ──
        moon_bonus = 0.02 if moon in ("Māuri", "Ōturu", "Rākaunui") else 0.0
        if pohatu.mode == "restorative":
            pohatu.mana = min(1.0, pohatu.mana + 0.01 + moon_bonus)
        else:
            pohatu.mana = max(0.0, pohatu.mana - 0.01)
            pohatu.tapu_charge = min(1.0, pohatu.tapu_charge + 0.005)

        # ── maramataka advances every 5 turns ──
        if turn % 5 == 4:
            new_moon = advance_moon(local)
            typewrite(f"\n  ☽  Maramataka turns → {new_moon}", 0.015)
            time.sleep(0.3)

        # ── auto-save ──
        local.save()
        mesh.save()
        turn += 1


def _victory(pohatu: PohaturState, local: LocalMemory, mesh: NonlocalMesh) -> None:
    clear()
    typewrite("\n" + "★" * 52, 0.01)
    typewrite("  KUA ORA TE AO PŌ", 0.04)
    typewrite("  All nine stars of Matariki are home.", 0.025)
    typewrite("  The whenua breathes. The pōhatu rests.", 0.025)
    typewrite("★" * 52, 0.01)
    print()
    typewrite(f"  Ora events:    {local.ora_events}", 0.01)
    typewrite(f"  Utu events:    {local.utu_events}", 0.01)
    typewrite(f"  Kawakawa planted: {len(local.kawakawa_planted)}", 0.01)
    typewrite(f"  Community mana: {round(mesh.community_mana*100)}%", 0.01)
    typewrite(f"  Mesh corruption: {round(mesh.corruption_level*100)}%", 0.01)
    print()
    typewrite("  Tūturu whakamaua kia tīna. Tīna! Hui e! Tāiki e!", 0.02)
    print()
    # reset for next run
    local.matariki_reunited.clear()
    local.save()
