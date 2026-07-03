import unittest
from chromaplex_os.assembler import assemble
from chromaplex_os.vm import VirtualMachine

class TestAssembler(unittest.TestCase):
    def test_mov_immediate(self):
        asm = """start:
            MOV R0, 42
            HALT"""
        bytecode = assemble(asm)
        vm = VirtualMachine()
        vm.load_program(bytecode)
        vm.run()
        self.assertEqual(vm.registers[0], 42)

    def test_store_load(self):
        asm = """MOV R0, 123
            SET_COLOR GREEN
            POSITION 5, 5, 5
            LASER_WRITE R0
            LASER_READ R1
            HALT"""
        bc = assemble(asm)
        vm = VirtualMachine()
        vm.load_program(bc)
        vm.run()
        self.assertEqual(vm.registers[1], 123)

if __name__ == "__main__":
    unittest.main()
