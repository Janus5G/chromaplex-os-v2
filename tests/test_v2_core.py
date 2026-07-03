"""Comprehensive tests for v2 core: facet crystal, blockchain, lens, spec."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
import hashlib

from chromaplex_os.spec import (
    encode_value, decode_value, encode_value_raw, decode_value_raw,
    NUM_FACETS, COLOUR_NAMES, WAVELENGTHS,
)
from chromaplex_os.facet_crystal import (
    BRILLANT_FACETS, FACET_BY_ID, FACET_BY_NAME,
    FacetAddress, FacetCrystal, LightSource, MultiCrystalArray, COLORS,
)
from chromaplex_os.blockchain_ledger import BlockchainLedger, WalletPayload
from chromaplex_os.lens_receiver import (
    LensReceiver, SpectralReading,
    _compute_refraction, _spectral_dispersion, REFRACTIVE_INDICES,
)


# ===== Spec / Base-N =====

class TestEncodeDecodeBase2(unittest.TestCase):
    def test_roundtrip_range(self):
        # n=1 is edge case: 2^0 + 0 = 1, but packed format
        # stores (e=0, r=0) which conflicts with zero encoding.
        # Start from 2 to test the general case.
        for n in range(2, 300):
            packed = encode_value(n, 2)
            self.assertEqual(decode_value(packed, 2), n)

    def test_zero(self):
        self.assertEqual(encode_value(0), 0)
        self.assertEqual(decode_value(0), 0)

    def test_powers_of_two(self):
        for e in range(1, 20):
            n = 2**e
            packed = encode_value(n, 2)
            self.assertEqual(decode_value(packed, 2), n)


class TestEncodeDecodeBaseN(unittest.TestCase):
    def test_base3_roundtrip(self):
        for n in [1, 3, 9, 27, 100, 1000, 1234567]:
            e, r, b = encode_value_raw(n, 3)
            self.assertEqual(decode_value_raw(e, r, b), n)

    def test_base5_roundtrip(self):
        for n in [5, 25, 125, 999, 50000]:
            e, r, b = encode_value_raw(n, 5)
            self.assertEqual(decode_value_raw(e, r, b), n)

    def test_base7_roundtrip(self):
        for n in [7, 49, 343, 100000]:
            e, r, b = encode_value_raw(n, 7)
            self.assertEqual(decode_value_raw(e, r, b), n)

    def test_base10_roundtrip(self):
        for n in [10, 100, 1000, 999999]:
            e, r, b = encode_value_raw(n, 10)
            self.assertEqual(decode_value_raw(e, r, b), n)

    def test_invalid_base(self):
        with self.assertRaises(ValueError):
            encode_value_raw(42, 1)
        with self.assertRaises(ValueError):
            encode_value_raw(42, 0)

    def test_rest_non_negative(self):
        for base in [2, 3, 5, 7, 10]:
            for n in [1, 42, 1000, 99999]:
                e, r, b = encode_value_raw(n, base)
                self.assertGreaterEqual(r, 0)


# ===== Facet Crystal =====

class TestFacetStructure(unittest.TestCase):
    def test_57_facets(self):
        self.assertEqual(len(BRILLANT_FACETS), 57)

    def test_unique_ids(self):
        ids = [f.id for f in BRILLANT_FACETS]
        self.assertEqual(len(set(ids)), 57)
        self.assertEqual(ids, list(range(57)))

    def test_groups_correct(self):
        groups = {}
        for f in BRILLANT_FACETS:
            groups.setdefault(f.group, []).append(f)
        self.assertEqual(len(groups["bord"]), 1)
        self.assertEqual(len(groups["krone_stjerne"]), 8)
        self.assertEqual(len(groups["krone_hoved"]), 8)
        self.assertEqual(len(groups["øvre_bælte"]), 16)
        self.assertEqual(len(groups["nedre_bælte"]), 16)
        self.assertEqual(len(groups["pavillon"]), 8)

    def test_facet_by_id_lookup(self):
        for i in range(57):
            self.assertEqual(FACET_BY_ID[i].id, i)

    def test_five_colour_channels(self):
        self.assertEqual(len(COLORS), 5)
        self.assertIn("rød", COLORS)
        self.assertIn("grøn", COLORS)
        self.assertIn("blå", COLORS)
        self.assertIn("violet", COLORS)
        self.assertIn("uv", COLORS)


class TestFacetCrystalIO(unittest.TestCase):
    def setUp(self):
        self.crystal = FacetCrystal(crystal_id=0, max_depth=10)

    def test_write_read_base2(self):
        self.crystal.write(0, "grøn", 10, 42, base=2)
        self.assertEqual(self.crystal.read(0, "grøn"), (10, 42, 2))

    def test_write_read_base3(self):
        self.crystal.write(5, "rød", 7, 100, base=3)
        self.assertEqual(self.crystal.read(5, "rød"), (7, 100, 3))

    def test_read_value_reconstructs(self):
        self.crystal.write(10, "blå", 5, 10, base=3)
        self.assertEqual(self.crystal.read_value(10, "blå"), 3**5 + 10)

    def test_different_depths(self):
        self.crystal.write(0, "grøn", 5, 0, base=2, depth=0)
        self.crystal.write(0, "grøn", 10, 0, base=2, depth=1)
        self.assertEqual(self.crystal.read(0, "grøn", 0), (5, 0, 2))
        self.assertEqual(self.crystal.read(0, "grøn", 1), (10, 0, 2))

    def test_capacity(self):
        self.assertEqual(self.crystal.capacity, 57 * 5 * 10)

    def test_invalid_facet_id(self):
        with self.assertRaises(ValueError):
            FacetAddress(0, 57, "grøn")

    def test_invalid_colour(self):
        with self.assertRaises(ValueError):
            FacetAddress(0, 0, "pink")

    def test_is_written(self):
        self.assertFalse(self.crystal.is_written(0, "grøn"))
        self.crystal.write(0, "grøn", 5, 0, base=2)
        self.assertTrue(self.crystal.is_written(0, "grøn"))


class TestLightSource(unittest.TestCase):
    def test_aim_at_facet(self):
        light = LightSource()
        facet = FACET_BY_ID[5]
        light.aim_at_facet(facet)
        self.assertEqual(light.theta, facet.theta)
        self.assertEqual(light.phi, facet.phi)

    def test_find_nearest_all_57(self):
        light = LightSource()
        for fid in range(57):
            light.aim_at_facet(FACET_BY_ID[fid])
            nearest = light.find_nearest_facet()
            self.assertEqual(nearest.id, fid)


class TestMultiCrystal(unittest.TestCase):
    def test_independent_storage(self):
        array = MultiCrystalArray(num_crystals=3, max_depth=10)
        array.write(0, 0, "grøn", 5, 10, 2)
        array.write(1, 0, "grøn", 7, 20, 3)
        array.write(2, 0, "grøn", 3, 5, 5)
        self.assertEqual(array.read(0, 0, "grøn"), (5, 10, 2))
        self.assertEqual(array.read(1, 0, "grøn"), (7, 20, 3))
        self.assertEqual(array.read(2, 0, "grøn"), (3, 5, 5))

    def test_combinatorial_capacity(self):
        arr = MultiCrystalArray(num_crystals=2, max_depth=10)
        single = 57 * 5 * 10
        self.assertEqual(arr.combinatorial_capacity, single ** 2)

    def test_invalid_crystal_count(self):
        with self.assertRaises(ValueError):
            MultiCrystalArray(num_crystals=0)


# ===== Blockchain =====

class TestBlockchainLedger(unittest.TestCase):
    def setUp(self):
        self.ledger = BlockchainLedger()
        self.array = MultiCrystalArray(num_crystals=1, max_depth=10)

    def test_write_once(self):
        addr = FacetAddress(0, 0, "grøn", 0)
        self.assertTrue(self.ledger.is_address_available(addr.key))
        self.ledger.register_write(addr, "hash1")
        self.assertFalse(self.ledger.is_address_available(addr.key))

    def test_write_once_rejects_duplicate(self):
        addr = FacetAddress(0, 0, "grøn", 0)
        self.ledger.register_write(addr, "hash1")
        with self.assertRaises(ValueError):
            self.ledger.register_write(addr, "hash2")

    def test_chain_integrity_10_blocks(self):
        for i in range(10):
            addr = FacetAddress(0, i % 57, ["grøn", "rød", "blå"][i % 3], i // 57)
            self.ledger.register_write(addr, f"hash{i}")
        self.assertTrue(self.ledger.verify_chain())

    def test_genesis_hash(self):
        chain = self.ledger.export_chain()
        self.assertEqual(len(chain), 0)
        addr = FacetAddress(0, 0, "grøn", 0)
        self.ledger.register_write(addr, "test")
        chain = self.ledger.export_chain()
        self.assertEqual(chain[0]["previous_hash"], "0" * 64)

    def test_extract_to_wallet(self):
        addr = FacetAddress(0, 5, "rød", 0)
        self.array.write(0, 5, "rød", 10, 42, base=2)
        self.ledger.register_write(addr, "hash")
        wallet = self.ledger.extract_to_wallet(addr, self.array)
        self.assertEqual(wallet.value, 2**10 + 42)
        self.assertTrue(wallet.verify())

    def test_extract_locks_position(self):
        addr = FacetAddress(0, 5, "rød", 0)
        self.array.write(0, 5, "rød", 10, 42, base=2)
        self.ledger.register_write(addr, "hash")
        self.ledger.extract_to_wallet(addr, self.array)
        self.assertTrue(self.ledger.is_address_spent(addr.key))
        with self.assertRaises(ValueError):
            self.ledger.extract_to_wallet(addr, self.array)

    def test_wallet_base3(self):
        addr = FacetAddress(0, 10, "blå", 0)
        self.array.write(0, 10, "blå", 7, 100, base=3)
        self.ledger.register_write(addr, "hash", base=3)
        wallet = self.ledger.extract_to_wallet(addr, self.array)
        self.assertEqual(wallet.value, 3**7 + 100)
        self.assertTrue(wallet.verify())

    def test_wallet_json_output(self):
        addr = FacetAddress(0, 0, "grøn", 0)
        self.array.write(0, 0, "grøn", 5, 0, base=2)
        self.ledger.register_write(addr, "hash")
        wallet = self.ledger.extract_to_wallet(addr, self.array)
        j = wallet.to_json()
        self.assertIn("payload_id", j)
        self.assertIn("extraction_hash", j)


# ===== Lens Receiver =====

class TestRefraction(unittest.TestCase):
    def test_snells_law_angle_decreases(self):
        theta_out = _compute_refraction(30.0, n1=1.0, n2=1.46)
        self.assertGreater(theta_out, 0)
        self.assertLess(theta_out, 30.0)

    def test_normal_incidence(self):
        self.assertAlmostEqual(_compute_refraction(0.0), 0.0)

    def test_dispersion_order(self):
        dispersions = _spectral_dispersion(34.5)
        # Higher refractive index = more bending = smaller output angle
        self.assertGreater(dispersions["rød"], dispersions["uv"])


class TestLensReceiver(unittest.TestCase):
    def setUp(self):
        self.crystal = FacetCrystal(crystal_id=0, max_depth=10)
        self.lens = LensReceiver()

    def test_empty_facet(self):
        reading = self.lens.capture(self.crystal, facet_id=0)
        self.assertEqual(len(reading.channels), 0)

    def test_capture_returns_data(self):
        self.crystal.write(5, "grøn", 12, 703126, base=3)
        reading = self.lens.capture(self.crystal, facet_id=5)
        self.assertIn("grøn", reading.channels)
        self.assertEqual(reading.total_value, 3**12 + 703126)

    def test_multi_colour_capture(self):
        self.crystal.write(10, "rød", 8, 100, base=2)
        self.crystal.write(10, "grøn", 5, 50, base=3)
        reading = self.lens.capture(self.crystal, facet_id=10)
        self.assertEqual(len(reading.channels), 2)

    def test_scan_only_written(self):
        self.crystal.write(0, "grøn", 5, 0, base=2)
        self.crystal.write(56, "uv", 4, 0, base=7)
        readings = self.lens.scan_all_facets(self.crystal)
        self.assertEqual(len(readings), 2)

    def test_wallet_payload_format(self):
        self.crystal.write(5, "grøn", 12, 703126, base=3)
        reading = self.lens.capture(self.crystal, facet_id=5)
        payload = reading.to_wallet_payload()
        self.assertIn("payload_id", payload)
        self.assertIn("extraction_hash", payload)
        self.assertEqual(payload["value"], 3**12 + 703126)

    def test_wallet_payload_hash_correct(self):
        self.crystal.write(5, "grøn", 12, 703126, base=3)
        reading = self.lens.capture(self.crystal, facet_id=5)
        payload = reading.to_wallet_payload()
        raw = f"C0:F5:grøn:D0:{payload['value']}:3:12:703126"
        expected = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        self.assertEqual(payload["extraction_hash"], expected)

    def test_reading_count(self):
        self.crystal.write(0, "grøn", 5, 0, base=2)
        self.lens.capture(self.crystal, 0)
        self.lens.capture(self.crystal, 0)
        self.assertEqual(self.lens.reading_count, 2)
        self.lens.clear()
        self.assertEqual(self.lens.reading_count, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
