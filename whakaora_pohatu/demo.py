"""
demo.py — non-interactive render test.
Renders one frame of each scene and prints to stdout without waiting for input.
Run: python -m whakaora_pohatu.demo
"""

from __future__ import annotations

from .engine import LocalMemory, NonlocalMesh, PohaturState
from .scenes import KoruGroveScene, MatarikiScene, TaniwhaScene
from .engine import MARAMATAKA_PHASES, MATARIKI_STARS


def main() -> None:
    local  = LocalMemory()
    mesh   = NonlocalMesh(community_mana=0.65, corruption_level=0.12)
    pohatu = PohaturState(mana=0.72)

    # ── Grove — restorative ──
    print("\n" + "=" * 52)
    print("DEMO RENDER: Koru Grove (restorative)")
    print("=" * 52)
    grove = KoruGroveScene(moon_phase=MARAMATAKA_PHASES[4])
    for line in grove.render(pohatu, local, mesh):
        print(line)
    print("\nChoices:")
    for cmd, desc in grove.choices(pohatu, local, mesh):
        print(f"  {cmd:<25} {desc}")

    # ── Grove — chaotic ──
    pohatu.toggle("chaotic")
    pohatu.tapu_charge = 0.55
    print("\n" + "=" * 52)
    print("DEMO RENDER: Koru Grove (chaotic)")
    print("=" * 52)
    for line in grove.render(pohatu, local, mesh):
        print(line)

    # ── Taniwha ──
    print("\n" + "=" * 52)
    print("DEMO RENDER: Taniwha (hostile)")
    print("=" * 52)
    pohatu.toggle("restorative")
    pohatu.tapu_charge = 0.2
    t = TaniwhaScene(mood="hostile")
    for line in t.render(pohatu, local, mesh):
        print(line)

    # ── Matariki ──
    print("\n" + "=" * 52)
    print("DEMO RENDER: Matariki (3 stars home)")
    print("=" * 52)
    local.matariki_reunited = MATARIKI_STARS[:3]
    m = MatarikiScene(stars_remaining=MATARIKI_STARS[3:])
    for line in m.render(pohatu, local, mesh):
        print(line)

    print("\n[demo complete — run `python -m whakaora_pohatu` for interactive play]")


if __name__ == "__main__":
    main()
