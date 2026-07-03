"""ChromaPlex Virtual Machine - udfører CPA bytecode mod simuleret krystallager.

v2: Udvidet med facet-krystal, blockchain-ledger, linsemodtager og base-N.
"""

import hashlib

from .spec import (
    Opcode, NUM_REGISTERS, DIM_X, DIM_Y, DIM_Z, WAVELENGTH_LIST, COLOUR_NAMES_REVERSE,
    encode_value, decode_value, encode_value_raw, decode_value_raw
)
from .storage import CrystalStorage
from .hardware import LaserControl
from .facet_crystal import (
    FACET_BY_ID, FacetAddress, FacetCrystal, MultiCrystalArray
)
from .blockchain_ledger import BlockchainLedger
from .lens_receiver import LensReceiver


class VirtualMachine:
    def __init__(self, storage=None, num_crystals=1, max_depth=10):
        # Legacy voxel-lagring
        self.storage = storage if storage else CrystalStorage(DIM_X, DIM_Y, DIM_Z)
        self.laser = LaserControl()

        # v2: Facetteret krystal + blockchain + linse
        self.crystal_array = MultiCrystalArray(num_crystals, max_depth)
        self.ledger = BlockchainLedger()
        self.lens = LensReceiver()

        # Registre og tilstand
        self.registers = [0] * NUM_REGISTERS
        self.reg_base = [2] * NUM_REGISTERS  # v2: base pr. register
        self.pc = 0
        self.running = False
        self.program = b''
        self.call_stack = []
        self.current_colour = 2  # GREEN default
        self.pos_x = 0
        self.pos_y = 0
        self.pos_z = 0

        # v2: Output-buffere
        self.output_buffer = []
        self.wallet_buffer = []
        self.lens_readings = []
        self.lens_payloads = []

    def load_program(self, bytecode: bytes):
        self.program = bytecode
        self.pc = 0

    def run(self):
        self.running = True
        max_steps = 100_000
        steps = 0
        while self.running and self.pc < len(self.program):
            self.step()
            steps += 1
            if steps > max_steps:
                raise RuntimeError("Maks antal trin overskredet")

    def step(self):
        if self.pc >= len(self.program):
            self.running = False
            return
        opcode_byte = self.program[self.pc]
        self.pc += 1
        try:
            opcode = Opcode(opcode_byte)
        except ValueError:
            raise RuntimeError(f"Ugyldig opcode 0x{opcode_byte:02X} ved PC={self.pc-1}")

        # === v1 originale instruktioner ===
        if opcode == Opcode.NOP:
            pass
        elif opcode == Opcode.HALT:
            self.running = False
        elif opcode == Opcode.LOAD:
            reg = self.program[self.pc]; self.pc += 1
            addr = int.from_bytes(self.program[self.pc:self.pc+4], 'big'); self.pc += 4
            x, y, z = self._linear_to_voxel(addr)
            value = self.storage.read_voxel(x, y, z, self.current_colour)
            self.registers[reg] = value
        elif opcode == Opcode.STORE:
            reg = self.program[self.pc]; self.pc += 1
            addr = int.from_bytes(self.program[self.pc:self.pc+4], 'big'); self.pc += 4
            x, y, z = self._linear_to_voxel(addr)
            value = self.registers[reg]
            self.storage.write_voxel(x, y, z, self.current_colour, value)
        elif opcode == Opcode.MOV:
            flag = self.program[self.pc]; self.pc += 1
            dst = self.program[self.pc]; self.pc += 1
            if flag == 0:
                src = self.program[self.pc]; self.pc += 1
                self.registers[dst] = self.registers[src]
                self.reg_base[dst] = self.reg_base[src]
            else:
                imm = int.from_bytes(self.program[self.pc:self.pc+4], 'big'); self.pc += 4
                self.registers[dst] = imm
                self.reg_base[dst] = 2
        elif opcode == Opcode.ADD:
            dst = self.program[self.pc]; self.pc += 1
            src = self.program[self.pc]; self.pc += 1
            self.registers[dst] += self.registers[src]
        elif opcode == Opcode.SUB:
            dst = self.program[self.pc]; self.pc += 1
            src = self.program[self.pc]; self.pc += 1
            self.registers[dst] -= self.registers[src]
        elif opcode == Opcode.MUL:
            dst = self.program[self.pc]; self.pc += 1
            src = self.program[self.pc]; self.pc += 1
            self.registers[dst] *= self.registers[src]
        elif opcode == Opcode.DIV:
            dst = self.program[self.pc]; self.pc += 1
            src = self.program[self.pc]; self.pc += 1
            if self.registers[src] == 0:
                raise ZeroDivisionError("Division med nul")
            self.registers[dst] //= self.registers[src]
        elif opcode == Opcode.ENCODE:
            reg = self.program[self.pc]; self.pc += 1
            self.registers[reg] = encode_value(self.registers[reg])
        elif opcode == Opcode.DECODE:
            reg = self.program[self.pc]; self.pc += 1
            self.registers[reg] = decode_value(self.registers[reg])
        elif opcode == Opcode.JMP:
            addr = int.from_bytes(self.program[self.pc:self.pc+4], 'big'); self.pc += 4
            self.pc = addr
        elif opcode == Opcode.JZ:
            reg = self.program[self.pc]; self.pc += 1
            addr = int.from_bytes(self.program[self.pc:self.pc+4], 'big'); self.pc += 4
            if self.registers[reg] == 0:
                self.pc = addr
        elif opcode == Opcode.JNZ:
            reg = self.program[self.pc]; self.pc += 1
            addr = int.from_bytes(self.program[self.pc:self.pc+4], 'big'); self.pc += 4
            if self.registers[reg] != 0:
                self.pc = addr
        elif opcode == Opcode.CALL:
            addr = int.from_bytes(self.program[self.pc:self.pc+4], 'big'); self.pc += 4
            self.call_stack.append(self.pc)
            self.pc = addr
        elif opcode == Opcode.RET:
            if not self.call_stack:
                self.running = False
            else:
                self.pc = self.call_stack.pop()
        elif opcode == Opcode.SET_COLOR:
            idx = self.program[self.pc]; self.pc += 1
            self.current_colour = idx
            wl = WAVELENGTH_LIST[idx]
            self.laser.set_wavelength(wl)
        elif opcode == Opcode.SET_POWER:
            reg = self.program[self.pc]; self.pc += 1
            power = self.registers[reg]
            self.laser.set_power(power)
        elif opcode == Opcode.POSITION:
            x = int.from_bytes(self.program[self.pc:self.pc+2], 'big'); self.pc += 2
            y = int.from_bytes(self.program[self.pc:self.pc+2], 'big'); self.pc += 2
            z = int.from_bytes(self.program[self.pc:self.pc+2], 'big'); self.pc += 2
            self.pos_x = x; self.pos_y = y; self.pos_z = z
            self.laser.move_to(x, y, z)
        elif opcode == Opcode.LASER_WRITE:
            reg = self.program[self.pc]; self.pc += 1
            value = self.registers[reg]
            self.laser.write_pulse()
            self.storage.write_voxel(self.pos_x, self.pos_y, self.pos_z, self.current_colour, value)
        elif opcode == Opcode.LASER_READ:
            reg = self.program[self.pc]; self.pc += 1
            self.laser.read_pulse()
            value = self.storage.read_voxel(self.pos_x, self.pos_y, self.pos_z, self.current_colour)
            self.registers[reg] = value
        elif opcode == Opcode.WAIT:
            ms = int.from_bytes(self.program[self.pc:self.pc+2], 'big'); self.pc += 2

        # === v2 nye instruktioner ===
        elif opcode == Opcode.ENCODE_N:
            reg = self.program[self.pc]; self.pc += 1
            base = self.program[self.pc]; self.pc += 1
            self.registers[reg] = encode_value(self.registers[reg], base)
            self.reg_base[reg] = base
        elif opcode == Opcode.DECODE_N:
            reg = self.program[self.pc]; self.pc += 1
            base = self.program[self.pc]; self.pc += 1
            self.registers[reg] = decode_value(self.registers[reg], base)
            self.reg_base[reg] = base

        elif opcode == Opcode.STORE_FACET:
            # Format: crystal(1) facet(1) colour(1) depth(2) reg(1)
            cid = self.program[self.pc]; self.pc += 1
            fid = self.program[self.pc]; self.pc += 1
            colour = self.program[self.pc]; self.pc += 1
            depth = int.from_bytes(self.program[self.pc:self.pc+2], 'big'); self.pc += 2
            reg = self.program[self.pc]; self.pc += 1

            value = self.registers[reg]
            base = self.reg_base[reg]
            e, rest, base = encode_value_raw(value, base)

            colour_name = COLOUR_NAMES_REVERSE[colour]
            addr = FacetAddress(cid, fid, colour_name.lower().replace("green", "grøn").replace("red", "rød").replace("blue", "blå"), depth)

            if not self.ledger.is_address_available(addr.key):
                raise RuntimeError(f"Position {addr.key} er låst — write-once")

            self.crystal_array.write(cid, fid, addr.color, e, rest, base, depth)
            data_hash = hashlib.sha256(f"{e}:{rest}:{base}".encode()).hexdigest()
            self.ledger.register_write(addr, data_hash, base)

        elif opcode == Opcode.LOAD_FACET:
            # Format: reg(1) crystal(1) facet(1) colour(1) depth(2)
            reg = self.program[self.pc]; self.pc += 1
            cid = self.program[self.pc]; self.pc += 1
            fid = self.program[self.pc]; self.pc += 1
            colour = self.program[self.pc]; self.pc += 1
            depth = int.from_bytes(self.program[self.pc:self.pc+2], 'big'); self.pc += 2

            colour_name = COLOUR_NAMES_REVERSE[colour]
            cn = colour_name.lower().replace("green", "grøn").replace("red", "rød").replace("blue", "blå")
            e, rest, base = self.crystal_array.read(cid, fid, cn, depth)
            self.registers[reg] = decode_value_raw(e, rest, base)
            self.reg_base[reg] = base

        elif opcode == Opcode.EXTRACT:
            # Format: crystal(1) facet(1) colour(1) depth(2)
            cid = self.program[self.pc]; self.pc += 1
            fid = self.program[self.pc]; self.pc += 1
            colour = self.program[self.pc]; self.pc += 1
            depth = int.from_bytes(self.program[self.pc:self.pc+2], 'big'); self.pc += 2

            colour_name = COLOUR_NAMES_REVERSE[colour]
            cn = colour_name.lower().replace("green", "grøn").replace("red", "rød").replace("blue", "blå")
            addr = FacetAddress(cid, fid, cn, depth)
            wallet = self.ledger.extract_to_wallet(addr, self.crystal_array)
            self.wallet_buffer.append(wallet)
            self.output_buffer.append(wallet.value)

        elif opcode == Opcode.LIGHT_AIM:
            cid = self.program[self.pc]; self.pc += 1
            fid = self.program[self.pc]; self.pc += 1
            crystal = self.crystal_array.crystal(cid)
            crystal.light.aim_at_facet(FACET_BY_ID[fid])

        elif opcode == Opcode.LENS_CAPTURE:
            cid = self.program[self.pc]; self.pc += 1
            fid = self.program[self.pc]; self.pc += 1
            depth = int.from_bytes(self.program[self.pc:self.pc+2], 'big'); self.pc += 2
            crystal = self.crystal_array.crystal(cid)
            reading = self.lens.capture(crystal, fid, depth=depth)
            self.lens_readings.append(reading)
            self.output_buffer.append(reading.total_value if reading.channels else 0)

        elif opcode == Opcode.LENS_SCAN:
            cid = self.program[self.pc]; self.pc += 1
            crystal = self.crystal_array.crystal(cid)
            readings = self.lens.scan_all_facets(crystal)
            self.lens_readings.extend(readings)
            self.output_buffer.append(len(readings))

        elif opcode == Opcode.LENS_TO_CHAIN:
            count = 0
            for reading in self.lens_readings:
                if not reading.channels:
                    continue
                payload = reading.to_wallet_payload()
                for color, (exp, rest, base) in reading.channels.items():
                    addr = FacetAddress(reading.crystal_id, reading.facet_id, color, 0)
                    if self.ledger.is_address_available(addr.key):
                        dh = hashlib.sha256(f"{exp}:{rest}:{base}".encode()).hexdigest()
                        self.ledger.register_write(addr, dh, base)
                    if self.ledger.is_address_extractable(addr.key):
                        wallet = self.ledger.extract_to_wallet(addr, self.crystal_array)
                        self.wallet_buffer.append(wallet)
                        payload["ledger_proof"] = wallet.ledger_proof
                        count += 1
                self.lens_payloads.append(payload)
            self.lens_readings.clear()
            self.output_buffer.append(count)

        elif opcode == Opcode.CHAIN_VERIFY:
            is_valid = self.ledger.verify_chain()
            self.output_buffer.append(1 if is_valid else 0)

    def _linear_to_voxel(self, linear: int) -> tuple:
        z = linear // (DIM_X * DIM_Y)
        remainder = linear % (DIM_X * DIM_Y)
        y = remainder // DIM_X
        x = remainder % DIM_X
        return x, y, z

    def print_state(self):
        print(f"PC={self.pc}, registre: {self.registers}")
        print(f"Position: ({self.pos_x},{self.pos_y},{self.pos_z}), "
              f"farve={COLOUR_NAMES_REVERSE[self.current_colour]}")
        print(f"Blockchain: {self.ledger.chain_length} blokke, "
              f"wallets: {len(self.wallet_buffer)}")
