"""
Tests for Whakaora Pōhatu core engine and scene rendering.
Pure stdlib — no pytest required (but works with pytest too).
Run: python -m pytest tests/ -v
  or: python tests/test_whakaora.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from whakaora_pohatu.engine import (
    LocalMemory,
    NonlocalMesh,
    PohaturState,
    build_koru,
    mana_bar,
    merkle_hash,
)
from whakaora_pohatu.loop import (
    resolve_grove,
    resolve_matariki,
    resolve_taniwha,
)
from whakaora_pohatu.scenes import KoruGroveScene, MatarikiScene, TaniwhaScene
from whakaora_pohatu.engine import MATARIKI_STARS, MARAMATAKA_PHASES


class TestManaBar(unittest.TestCase):
    def test_full(self):
        bar = mana_bar(1.0, 10)
        self.assertEqual(bar, "█" * 10)

    def test_empty(self):
        bar = mana_bar(0.0, 10)
        self.assertEqual(bar, "░" * 10)

    def test_half(self):
        bar = mana_bar(0.5, 10)
        self.assertIn("█", bar)
        self.assertIn("░", bar)
        self.assertEqual(len(bar), 10)


class TestMerkleHash(unittest.TestCase):
    def test_deterministic(self):
        d = {"a": 1, "b": [2, 3]}
        self.assertEqual(merkle_hash(d), merkle_hash(d))

    def test_length(self):
        self.assertEqual(len(merkle_hash({})), 16)

    def test_different_on_change(self):
        self.assertNotEqual(merkle_hash({"x": 1}), merkle_hash({"x": 2}))


class TestPohaturState(unittest.TestCase):
    def test_toggle(self):
        p = PohaturState()
        p.toggle("chaotic")
        self.assertEqual(p.mode, "chaotic")
        p.toggle("restorative")
        self.assertEqual(p.mode, "restorative")

    def test_glyph_restorative_high_mana(self):
        p = PohaturState(mana=0.8)
        self.assertIn("🌿", p.glyph)

    def test_glyph_chaotic(self):
        p = PohaturState(mana=0.3)
        p.toggle("chaotic")
        self.assertIn(p.glyph, ["🔥", "☠"])


class TestBuildKoru(unittest.TestCase):
    def test_returns_list_of_strings(self):
        rows = build_koru(0.7, False, depth=3)
        self.assertIsInstance(rows, list)
        self.assertTrue(all(isinstance(r, str) for r in rows))

    def test_fixed_height(self):
        rows = build_koru(0.5, False, depth=2)
        self.assertEqual(len(rows), 20)

    def test_chaos_different_chars(self):
        import random as _r; _r.seed(42)
        normal = "".join(build_koru(0.9, False, depth=3))
        _r.seed(42)
        chaotic = "".join(build_koru(0.9, True, depth=3))
        # character sets differ — outputs should not be identical
        # (allow tiny chance of collision at seed 42, but structurally they differ)
        chaos_chars = set("!@#%^&*><\\|/~")
        self.assertTrue(any(c in chaotic for c in chaos_chars))


class TestNonlocalMesh(unittest.TestCase):
    def test_pulse_ora(self):
        mesh = NonlocalMesh(community_mana=0.5, corruption_level=0.2)
        mesh.pulse(ora_delta=1.0, utu_delta=0.0)
        self.assertGreater(mesh.community_mana, 0.5)
        self.assertLess(mesh.corruption_level, 0.2)

    def test_pulse_utu(self):
        mesh = NonlocalMesh(community_mana=0.5, corruption_level=0.2)
        mesh.pulse(ora_delta=0.0, utu_delta=1.0)
        self.assertLess(mesh.community_mana, 0.5)
        self.assertGreater(mesh.corruption_level, 0.2)

    def test_clamp(self):
        mesh = NonlocalMesh(community_mana=1.0, corruption_level=0.0)
        for _ in range(100):
            mesh.pulse(ora_delta=1.0, utu_delta=0.0)
        self.assertLessEqual(mesh.community_mana, 1.0)
        self.assertGreaterEqual(mesh.corruption_level, 0.0)


class TestResolveGrove(unittest.TestCase):
    def _setup(self):
        local  = LocalMemory()
        mesh   = NonlocalMesh()
        pohatu = PohaturState(mana=0.6)
        return local, mesh, pohatu

    def test_whakapapa_ora_raises_mana(self):
        local, mesh, pohatu = self._setup()
        before = pohatu.mana
        resolve_grove("whakapapa ora", pohatu, local, mesh, "Hoata")
        self.assertGreater(pohatu.mana, before)
        self.assertEqual(pohatu.mode, "restorative")

    def test_wero_chaos_costs_mana(self):
        local, mesh, pohatu = self._setup()
        before = pohatu.mana
        resolve_grove("wero chaos", pohatu, local, mesh, "Hoata")
        self.assertLess(pohatu.mana, before)
        self.assertEqual(pohatu.mode, "chaotic")
        self.assertGreater(pohatu.tapu_charge, 0.0)

    def test_tiaki_kawakawa_plants(self):
        local, mesh, pohatu = self._setup()
        resolve_grove("tiaki kawakawa", pohatu, local, mesh, "Hoata")
        self.assertEqual(len(local.kawakawa_planted), 1)

    def test_tiaki_kawakawa_needs_mana(self):
        local, mesh, pohatu = self._setup()
        pohatu.mana = 0.05
        result = resolve_grove("tiaki kawakawa", pohatu, local, mesh, "Hoata")
        self.assertIn("Not enough", result)
        self.assertEqual(len(local.kawakawa_planted), 0)

    def test_navigate_tokens(self):
        local, mesh, pohatu = self._setup()
        r1 = resolve_grove("karakia matariki", pohatu, local, mesh, "Hoata")
        r2 = resolve_grove("korero taniwha",   pohatu, local, mesh, "Hoata")
        self.assertEqual(r1, "navigate:matariki")
        self.assertEqual(r2, "navigate:taniwha")


class TestResolveTaniwha(unittest.TestCase):
    def _setup(self):
        local  = LocalMemory()
        mesh   = NonlocalMesh()
        pohatu = PohaturState(mana=0.6)
        scene  = TaniwhaScene(mood="curious")
        return local, mesh, pohatu, scene

    def test_karakia_appeases_curious(self):
        local, mesh, pohatu, scene = self._setup()
        resolve_taniwha("karakia awa", pohatu, local, mesh, scene)
        self.assertEqual(scene.mood, "appeased")

    def test_wero_angers_dormant(self):
        local, mesh, pohatu, scene = self._setup()
        scene.mood = "dormant"
        resolve_taniwha("wero", pohatu, local, mesh, scene)
        self.assertEqual(scene.mood, "hostile")

    def test_homai_taonga_costs_mana(self):
        local, mesh, pohatu, scene = self._setup()
        before = pohatu.mana
        resolve_taniwha("homai taonga", pohatu, local, mesh, scene)
        self.assertLess(pohatu.mana, before)

    def test_hoki_atu_navigates(self):
        local, mesh, pohatu, scene = self._setup()
        result = resolve_taniwha("hoki atu", pohatu, local, mesh, scene)
        self.assertEqual(result, "navigate:grove")


class TestResolveMatariki(unittest.TestCase):
    def _setup(self):
        local  = LocalMemory()
        mesh   = NonlocalMesh()
        pohatu = PohaturState(mana=0.6)
        return local, mesh, pohatu

    def test_call_star(self):
        local, mesh, pohatu = self._setup()
        result = resolve_matariki("karakia matariki", pohatu, local, mesh)
        self.assertIn("Matariki", local.matariki_reunited)

    def test_star_already_home(self):
        local, mesh, pohatu = self._setup()
        local.matariki_reunited.append("Matariki")
        result = resolve_matariki("karakia matariki", pohatu, local, mesh)
        self.assertIn("already home", result)

    def test_needs_mana(self):
        local, mesh, pohatu = self._setup()
        pohatu.mana = 0.05
        result = resolve_matariki("karakia waitī", pohatu, local, mesh)
        self.assertIn("Not enough", result)

    def test_all_nine_triggers_victory_message(self):
        local, mesh, pohatu = self._setup()
        local.matariki_reunited = MATARIKI_STARS[:8]
        mesh.matariki_aligned   = MATARIKI_STARS[:8]
        pohatu.mana = 1.0
        result = resolve_matariki("karakia hiwa-i-te-rangi", pohatu, local, mesh)
        self.assertIn("All nine", result)


class TestSceneRender(unittest.TestCase):
    def _ctx(self):
        local  = LocalMemory()
        mesh   = NonlocalMesh()
        pohatu = PohaturState()
        return local, mesh, pohatu

    def test_grove_render_returns_nonempty_list(self):
        local, mesh, pohatu = self._ctx()
        scene = KoruGroveScene(moon_phase="Hoata")
        lines = scene.render(pohatu, local, mesh)
        self.assertIsInstance(lines, list)
        self.assertGreater(len(lines), 5)

    def test_taniwha_render(self):
        local, mesh, pohatu = self._ctx()
        scene = TaniwhaScene(mood="appeased")
        lines = scene.render(pohatu, local, mesh)
        self.assertTrue(any("appeased" in l.lower() or "head" in l.lower()
                            for l in lines))

    def test_matariki_render_shows_stars(self):
        local, mesh, pohatu = self._ctx()
        scene = MatarikiScene(stars_remaining=MATARIKI_STARS)
        lines = scene.render(pohatu, local, mesh)
        joined = " ".join(lines)
        self.assertIn("Matariki", joined)


if __name__ == "__main__":
    unittest.main(verbosity=2)
