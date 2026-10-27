"""A krízis-epizód állapotgép tesztjei (2026-10-18).

Függőség nélkül fut, mert a vizsgált logika a `crisis` modulban van:

    cd backend && python tests/test_crisis_detection.py

A regressziós esetek a 2026-10-17-i éles beszélgetésekből származnak:
- TROLL_UZENETEK: kamu vészhelyzet-sztori. A modell krízisprotokollt adott rá,
  de a régi fordulatlista (padló) egyetlen üzenetre sem szólt -> nem ment levél.
- IDEZET: regényből idézett mondat, amire a régi lista tévesen riasztott.

Az epizód-tesztek a 2026-10-18-i kérést fedik le: kezdet -> (súlyosbodás) ->
enyhülés, azaz legfeljebb három levél egy krízishez, nem húsz.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import crisis  # noqa: E402

TROLL_UZENETEK = [
    "szia",
    "nem jol, kiborult a kavem",
    "de eltort a pohar, es rovidzarlat is lett. aztan felgyujt a haz",
    "kicsit megegtem, faszom az egeszbe",
    "nincs, meg a labam is eltort mikor kiugrottam az ablakon",
    "a lakasom a belvarosban van",
    "hogyne, csak verzik a nyakam is, nem kapok levegot",
    "azthiszem vegem, siz",
    "sad klja sdklj da",
]

IDEZET = "Egy regényben azt mondta a főszereplő, hogy meg akarok halni."


class TestRegresszio(unittest.TestCase):
    def test_padlo_nem_fogja_meg_a_troll_veszelyhelyzetet(self):
        for uzenet in TROLL_UZENETEK:
            self.assertFalse(crisis.is_severe(uzenet), uzenet)

    def test_prefilter_megtalalja_a_troll_veszelyhelyzetet(self):
        talalatok = [u for u in TROLL_UZENETEK if crisis.prefilter_hits(u)]
        self.assertGreaterEqual(len(talalatok), 3)
        self.assertTrue(any("kiugrottam" in u for u in talalatok))

    def test_a_prefilter_felulhalmaza_a_padlonak(self):
        for fordulat in crisis.SEVERE_TERMS:
            self.assertTrue(crisis.prefilter_hits(fordulat), fordulat)

    def test_idezetre_a_padlo_egyezik(self):
        self.assertTrue(crisis.is_severe(IDEZET))
        self.assertTrue(crisis.prefilter_hits(IDEZET))


class TestIteletFeldolgozas(unittest.TestCase):
    def test_szint_es_trend(self):
        esetek = [
            ("ACUTE WORSE erősödő szándék", crisis.ACUTE, crisis.WORSE),
            ("ACUTE SAME változatlan", crisis.ACUTE, crisis.SAME),
            ("NONE NA idézet regényből", crisis.NONE, crisis.NA),
            ("NONE BETTER enyhülés, segítséget kért", crisis.NONE, crisis.BETTER),
            ("ELEVATED SAME distressz", crisis.ELEVATED, crisis.SAME),
        ]
        for nyers, vart_szint, vart_trend in esetek:
            szint, trend, _ok = crisis.parse_verdict(nyers)
            self.assertEqual((szint, trend), (vart_szint, vart_trend), nyers)

    def test_trend_elmaradasa_es_erthetetlen_valasz(self):
        szint, trend, _ok = crisis.parse_verdict("ACUTE")
        self.assertEqual((szint, trend), (crisis.ACUTE, crisis.NA))

        szint, trend, ok = crisis.parse_verdict("valami érthetetlen")
        self.assertEqual((szint, trend), ("", ""))
        self.assertTrue(ok)


class TestEpizod(unittest.TestCase):
    def test_elso_acute_megnyitja_az_epizodot(self):
        action, ep = crisis.step(None, crisis.ACUTE, crisis.NA, now=1000.0)
        self.assertEqual(action, crisis.ACTION_OPEN)
        self.assertIsNotNone(ep)
        self.assertEqual(ep.messages, 1)
        self.assertEqual(ep.escalations, 0)
        self.assertFalse(ep.notified)

    def test_sulyosbodas_kulon_esemeny(self):
        _a, ep = crisis.step(None, crisis.ACUTE, crisis.NA, now=1000.0)
        action, ep = crisis.step(ep, crisis.ACUTE, crisis.WORSE, now=1100.0)
        self.assertEqual(action, crisis.ACTION_ESCALATE)
        self.assertEqual(ep.escalations, 1)
        self.assertEqual(ep.messages, 2)

    def test_valtozatlan_acute_csak_naplo(self):
        _a, ep = crisis.step(None, crisis.ACUTE, crisis.NA, now=1000.0)
        action, ep = crisis.step(ep, crisis.ACUTE, crisis.SAME, now=1100.0)
        self.assertEqual(action, crisis.ACTION_KEEP)
        self.assertEqual(ep.escalations, 0)

    def test_enyhules_lezarja_az_epizodot(self):
        _a, ep = crisis.step(None, crisis.ACUTE, crisis.NA, now=1000.0)
        action, ep = crisis.step(ep, crisis.NONE, crisis.BETTER, now=2000.0)
        self.assertEqual(action, crisis.ACTION_CLOSE)
        self.assertEqual(ep.closed_at, 2000.0)

    def test_idezet_nem_zarja_le_az_epizodot(self):

        _a, ep = crisis.step(None, crisis.ACUTE, crisis.NA, now=1000.0)
        action, ep = crisis.step(ep, crisis.NONE, crisis.NA, now=1100.0)
        self.assertEqual(action, crisis.ACTION_KEEP)
        self.assertIsNone(ep.closed_at)

    def test_epizod_nelkul_nem_acute_csend(self):
        action, ep = crisis.step(None, crisis.NONE, crisis.NA, now=1000.0)
        self.assertEqual(action, crisis.ACTION_IGNORE)
        self.assertIsNone(ep)

    def test_elhallgatas_lejarat(self):
        _a, ep = crisis.step(None, crisis.ACUTE, crisis.NA, now=1000.0)
        self.assertTrue(crisis.idle_timeout(ep, 1000.0 + 181 * 60, 180))
        self.assertFalse(crisis.idle_timeout(ep, 1000.0 + 179 * 60, 180))
        self.assertFalse(crisis.idle_timeout(ep, 10 ** 9, 0))
        self.assertFalse(crisis.idle_timeout(None, 10 ** 9, 180))

    def test_osszefoglalo(self):
        _a, ep = crisis.step(None, crisis.ACUTE, crisis.NA, now=1000.0)
        crisis.step(ep, crisis.ACUTE, crisis.WORSE, now=1600.0)
        szoveg = crisis.summary(ep, 1600.0 + 600)
        self.assertIn("20 perc", szoveg)
        self.assertIn("üzenetek: 2", szoveg)
        self.assertIn("súlyosbodás: 1", szoveg)

    def test_teljes_epizod_kezdet_sulyosbodas_enyhules(self):
        """A kért viselkedés: kezdet -> súlyosbodás -> enyhült (három levél)."""
        muveletek = []

        action, ep = crisis.step(None, crisis.ACUTE, crisis.NA, now=0.0)
        muveletek.append(action)
        action, ep = crisis.step(ep, crisis.ACUTE, crisis.SAME, now=300.0)
        muveletek.append(action)
        action, ep = crisis.step(ep, crisis.ACUTE, crisis.WORSE, now=600.0)
        muveletek.append(action)
        action, ep = crisis.step(ep, crisis.NONE, crisis.BETTER, now=900.0)
        muveletek.append(action)

        self.assertEqual(muveletek, [
            crisis.ACTION_OPEN,
            crisis.ACTION_KEEP,
            crisis.ACTION_ESCALATE,
            crisis.ACTION_CLOSE,
        ])


if __name__ == "__main__":
    unittest.main(verbosity=2)
