"""Tests for ChromaPlex Python API."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
from chromaplex_os.api import ChromaPlex


class TestPythonAPI(unittest.TestCase):

    def test_store_load(self):
        cx = ChromaPlex()
        cx.store(facet=5, colour="GREEN", value=42)
        self.assertEqual(cx.load(facet=5, colour="GREEN"), 42)

    def test_store_base3(self):
        cx = ChromaPlex()
        cx.store(facet=10, colour="RED", value=1234567, base=3)
        self.assertEqual(cx.load(facet=10, colour="RED"), 1234567)

    def test_write_once(self):
        cx = ChromaPlex()
        cx.store(facet=0, colour="GREEN", value=100)
        with self.assertRaises(ValueError):
            cx.store(facet=0, colour="GREEN", value=200)

    def test_lens_capture(self):
        cx = ChromaPlex()
        cx.store(facet=5, colour="GREEN", value=777)
        vals = cx.lens_capture(facet=5)
        self.assertIn("grøn", vals)
        self.assertEqual(vals["grøn"], 777)

    def test_lens_scan(self):
        cx = ChromaPlex()
        cx.store(facet=0, colour="GREEN", value=100)
        cx.store(facet=20, colour="RED", value=200)
        count = cx.lens_scan()
        self.assertEqual(count, 2)

    def test_lens_to_chain(self):
        cx = ChromaPlex()
        cx.store(facet=5, colour="GREEN", value=500)
        cx.lens_capture(facet=5)
        payloads = cx.lens_to_chain()
        self.assertGreater(len(payloads), 0)
        self.assertEqual(payloads[0]["value"], 500)

    def test_extract(self):
        cx = ChromaPlex()
        cx.store(facet=10, colour="BLUE", value=9999, base=7)
        wallet = cx.extract(facet=10, colour="BLUE")
        self.assertEqual(wallet.value, 9999)
        self.assertTrue(wallet.verify())

    def test_chain_valid(self):
        cx = ChromaPlex()
        cx.store(facet=0, colour="GREEN", value=1)
        cx.store(facet=1, colour="GREEN", value=2)
        self.assertTrue(cx.chain_valid())

    def test_multi_crystal(self):
        cx = ChromaPlex(num_crystals=3)
        cx.store(facet=0, colour="GREEN", value=111, crystal=0)
        cx.store(facet=0, colour="GREEN", value=222, crystal=1)
        cx.store(facet=0, colour="GREEN", value=333, crystal=2)
        self.assertEqual(cx.load(facet=0, colour="GREEN", crystal=0), 111)
        self.assertEqual(cx.load(facet=0, colour="GREEN", crystal=1), 222)
        self.assertEqual(cx.load(facet=0, colour="GREEN", crystal=2), 333)

    def test_danish_colour_names(self):
        cx = ChromaPlex()
        cx.store(facet=5, colour="GRØN", value=42)
        self.assertEqual(cx.load(facet=5, colour="GRØN"), 42)

    def test_capacity(self):
        cx = ChromaPlex(num_crystals=2)
        cap = cx.capacity()
        self.assertEqual(cap["antal_krystaller"], 2)
        self.assertGreater(cap["kombinatorisk_kapacitet"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
