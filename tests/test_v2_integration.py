"""Tests for merged VM — v1 legacy + v2 facet/blockchain/lens bytecode."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
from chromaplex_os.assembler import assemble
from chromaplex_os.vm import VirtualMachine
from chromaplex_os.spec import encode_value, decode_value, encode_value_raw, decode_value_raw


class TestV1Legacy(unittest.TestCase):
    """Originale v1-instruktioner virker stadig."""

    def test_mov_add(self):
        asm = """
    MOV R0, 10
    MOV R1, 32
    ADD R0, R1
    HALT
"""
        vm = VirtualMachine()
        vm.load_program(assemble(asm))
        vm.run()
        self.assertEqual(vm.registers[0], 42)

    def test_store_load_voxel(self):
        asm = """
    MOV R0, 1234
    SET_COLOR GREEN
    POSITION 5, 5, 5
    LASER_WRITE R0
    LASER_READ R1
    HALT
"""
        vm = VirtualMachine()
        vm.load_program(assemble(asm))
        vm.run()
        self.assertEqual(vm.registers[1], 1234)

    def test_encode_decode(self):
        asm = """
    MOV R0, 170
    ENCODE R0
    DECODE R0
    HALT
"""
        vm = VirtualMachine()
        vm.load_program(assemble(asm))
        vm.run()
        self.assertEqual(vm.registers[0], 170)

    def test_jump(self):
        asm = """
    MOV R0, 0
    JMP skip
    MOV R0, 999
skip:
    MOV R1, 42
    HALT
"""
        vm = VirtualMachine()
        vm.load_program(assemble(asm))
        vm.run()
        self.assertEqual(vm.registers[0], 0)
        self.assertEqual(vm.registers[1], 42)


class TestBaseN(unittest.TestCase):
    """v2 base-N encode/decode."""

    def test_encode_n_bytecode(self):
        asm = """
    MOV R0, 1000
    ENCODE_N R0, 3
    DECODE_N R0, 3
    HALT
"""
        vm = VirtualMachine()
        vm.load_program(assemble(asm))
        vm.run()
        self.assertEqual(vm.registers[0], 1000)

    def test_encode_raw(self):
        e, r, b = encode_value_raw(1234567, 3)
        self.assertEqual(b**e + r, 1234567)
        self.assertEqual(b, 3)

    def test_decode_raw(self):
        val = decode_value_raw(12, 703126, 3)
        self.assertEqual(val, 3**12 + 703126)
        self.assertEqual(val, 1234567)


class TestFacetBytecode(unittest.TestCase):
    """v2 facet-instruktioner via bytecode."""

    def test_store_load_facet(self):
        asm = """
    MOV R0, 42
    STORE_FACET 0, 5, GREEN, 0, R0
    LOAD_FACET R1, 0, 5, GREEN, 0
    HALT
"""
        vm = VirtualMachine(num_crystals=1)
        vm.load_program(assemble(asm))
        vm.run()
        self.assertEqual(vm.registers[1], 42)

    def test_write_once_enforced(self):
        asm = """
    MOV R0, 42
    STORE_FACET 0, 0, RED, 0, R0
    STORE_FACET 0, 0, RED, 0, R0
    HALT
"""
        vm = VirtualMachine(num_crystals=1)
        vm.load_program(assemble(asm))
        with self.assertRaises(RuntimeError):
            vm.run()

    def test_extract_to_wallet(self):
        asm = """
    MOV R0, 1000
    STORE_FACET 0, 10, BLUE, 0, R0
    EXTRACT 0, 10, BLUE, 0
    CHAIN_VERIFY
    HALT
"""
        vm = VirtualMachine(num_crystals=1)
        vm.load_program(assemble(asm))
        vm.run()
        self.assertEqual(len(vm.wallet_buffer), 1)
        self.assertEqual(vm.wallet_buffer[0].value, 1000)
        self.assertTrue(vm.wallet_buffer[0].verify())
        self.assertEqual(vm.output_buffer[-1], 1)  # chain valid

    def test_multi_crystal(self):
        asm = """
    MOV R0, 100
    STORE_FACET 0, 0, GREEN, 0, R0
    MOV R0, 200
    STORE_FACET 1, 0, GREEN, 0, R0
    LOAD_FACET R1, 0, 0, GREEN, 0
    LOAD_FACET R2, 1, 0, GREEN, 0
    HALT
"""
        vm = VirtualMachine(num_crystals=2)
        vm.load_program(assemble(asm))
        vm.run()
        self.assertEqual(vm.registers[1], 100)
        self.assertEqual(vm.registers[2], 200)


class TestLensBytecode(unittest.TestCase):
    """v2 linse-instruktioner via bytecode."""

    def test_lens_capture(self):
        asm = """
    MOV R0, 500
    STORE_FACET 0, 20, RED, 0, R0
    LENS_CAPTURE 0, 20, 0
    HALT
"""
        vm = VirtualMachine(num_crystals=1)
        vm.load_program(assemble(asm))
        vm.run()
        self.assertEqual(len(vm.lens_readings), 1)
        self.assertGreater(vm.output_buffer[-1], 0)

    def test_lens_scan(self):
        asm = """
    MOV R0, 100
    STORE_FACET 0, 0, GREEN, 0, R0
    MOV R0, 200
    STORE_FACET 0, 30, BLUE, 0, R0
    LENS_SCAN 0
    HALT
"""
        vm = VirtualMachine(num_crystals=1)
        vm.load_program(assemble(asm))
        vm.run()
        self.assertEqual(vm.output_buffer[-1], 2)  # 2 facetter med data

    def test_full_lens_to_chain_pipeline(self):
        asm = """
    MOV R0, 777
    STORE_FACET 0, 5, GREEN, 0, R0
    LENS_CAPTURE 0, 5, 0
    LENS_TO_CHAIN
    CHAIN_VERIFY
    HALT
"""
        vm = VirtualMachine(num_crystals=1)
        vm.load_program(assemble(asm))
        vm.run()
        self.assertGreater(len(vm.wallet_buffer), 0)
        self.assertEqual(vm.output_buffer[-1], 1)  # chain valid


if __name__ == "__main__":
    unittest.main(verbosity=2)
