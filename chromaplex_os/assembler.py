"""Assembler til ChromaPlex Assembly (CPA) tekst-til-binær bytecode."""

import re
from typing import Dict, Tuple
from .spec import Opcode, COLOUR_NAMES, NUM_REGISTERS

LABEL_RE = re.compile(r"^([a-zA-Z_]\w*):\s*$")
INSTR_RE = re.compile(r"^\s+([A-Z]+)\s*(.*)$")

def assemble_line(line: str) -> Tuple[str, str, list]:
    line = line.strip()
    if not line or line.startswith("#"):
        return None, None, []
    m = LABEL_RE.match(line)
    if m:
        return m.group(1), None, []
    m = INSTR_RE.match(line)
    if m:
        mnemonic = m.group(1).upper()
        args_str = m.group(2)
        args = [a.strip() for a in args_str.split(",") if a.strip()] if args_str else []
        return None, mnemonic, args
    parts = line.split()
    if parts:
        mnemonic = parts[0].upper()
        args = parts[1:] if len(parts) > 1 else []
        if mnemonic in Opcode.__members__ or mnemonic in {"SET_COLOR", "SET_POWER", "POSITION", "LASER_WRITE", "LASER_READ", "WAIT", "JMP", "JZ", "JNZ", "CALL"}:
            args = [a.strip().rstrip(",") for a in args]
            return None, mnemonic, args
    raise SyntaxError(f"Ugyldig linje: {line}")

def parse_register(token: str) -> int:
    if not token.upper().startswith("R"):
        raise ValueError(f"Forventede register, fik {token}")
    idx = int(token[1:])
    if not 0 <= idx < NUM_REGISTERS:
        raise ValueError(f"Register indeks uden for område: {idx}")
    return idx

def parse_immediate(token: str) -> int:
    token = token.upper()
    if token.startswith("0X"):
        return int(token, 16)
    try:
        return int(token)
    except ValueError:
        raise ValueError(f"Forventede et tal, fik {token}")

def assemble(asm_text: str) -> bytes:
    """Assemblér CPA tekst til binær bytecode."""
    lines = asm_text.splitlines()
    labels: Dict[str, int] = {}
    offset = 0
    instructions = []
    for lineno, raw_line in enumerate(lines, 1):
        label, mnemonic, args = assemble_line(raw_line)
        if label:
            if label in labels:
                raise SyntaxError(f"Duplicate label '{label}' ved linje {lineno}")
            labels[label] = offset
        if mnemonic:
            instructions.append((mnemonic, args, lineno))
            offset += instruction_size(mnemonic, args)
    bytecode = bytearray()
    for mnemonic, args, lineno in instructions:
        try:
            opcode = Opcode[mnemonic]
        except KeyError:
            raise SyntaxError(f"Ukendt mnemonic '{mnemonic}' ved linje {lineno}")
        bytecode.append(opcode.value)
        if opcode in (Opcode.LOAD, Opcode.STORE):
            reg = parse_register(args[0])
            addr = parse_immediate(args[1])
            bytecode.append(reg)
            bytecode.extend(addr.to_bytes(4, 'big'))
        elif opcode == Opcode.MOV:
            dst = parse_register(args[0])
            if args[1].upper().startswith("R"):
                src = parse_register(args[1])
                bytecode.append(0)
                bytecode.append(dst)
                bytecode.append(src)
            else:
                imm = parse_immediate(args[1])
                bytecode.append(1)
                bytecode.append(dst)
                bytecode.extend(imm.to_bytes(4, 'big'))
        elif opcode in (Opcode.ADD, Opcode.SUB, Opcode.MUL, Opcode.DIV):
            dst = parse_register(args[0])
            src = parse_register(args[1])
            bytecode.append(dst)
            bytecode.append(src)
        elif opcode in (Opcode.ENCODE, Opcode.DECODE):
            reg = parse_register(args[0])
            bytecode.append(reg)
        elif opcode in (Opcode.JMP, Opcode.CALL):
            addr = labels[args[0]] if args[0] in labels else parse_immediate(args[0])
            bytecode.extend(addr.to_bytes(4, 'big'))
        elif opcode in (Opcode.JZ, Opcode.JNZ):
            reg = parse_register(args[0])
            addr = labels[args[1]] if args[1] in labels else parse_immediate(args[1])
            bytecode.append(reg)
            bytecode.extend(addr.to_bytes(4, 'big'))
        elif opcode == Opcode.RET:
            pass
        elif opcode == Opcode.SET_COLOR:
            colour = args[0].upper()
            idx = COLOUR_NAMES[colour] if colour in COLOUR_NAMES else parse_immediate(args[0])
            bytecode.append(idx)
        elif opcode == Opcode.SET_POWER:
            reg = parse_register(args[0])
            bytecode.append(reg)
        elif opcode == Opcode.POSITION:
            x = parse_immediate(args[0])
            y = parse_immediate(args[1])
            z = parse_immediate(args[2])
            bytecode.extend(x.to_bytes(2, 'big'))
            bytecode.extend(y.to_bytes(2, 'big'))
            bytecode.extend(z.to_bytes(2, 'big'))
        elif opcode in (Opcode.LASER_WRITE, Opcode.LASER_READ):
            reg = parse_register(args[0])
            bytecode.append(reg)
        elif opcode == Opcode.WAIT:
            ms = parse_immediate(args[0])
            bytecode.extend(ms.to_bytes(2, 'big'))
        # === v2 nye instruktioner ===
        elif opcode in (Opcode.ENCODE_N, Opcode.DECODE_N):
            reg = parse_register(args[0])
            base_val = parse_immediate(args[1])
            bytecode.append(reg)
            bytecode.append(base_val)
        elif opcode == Opcode.STORE_FACET:
            # crystal, facet, colour, depth, reg
            bytecode.append(parse_immediate(args[0]))  # crystal
            bytecode.append(parse_immediate(args[1]))  # facet
            colour = args[2].upper()
            bytecode.append(COLOUR_NAMES[colour] if colour in COLOUR_NAMES else parse_immediate(args[2]))
            depth = parse_immediate(args[3])
            bytecode.extend(depth.to_bytes(2, 'big'))
            bytecode.append(parse_register(args[4]))
        elif opcode == Opcode.LOAD_FACET:
            # reg, crystal, facet, colour, depth
            bytecode.append(parse_register(args[0]))
            bytecode.append(parse_immediate(args[1]))  # crystal
            bytecode.append(parse_immediate(args[2]))  # facet
            colour = args[3].upper()
            bytecode.append(COLOUR_NAMES[colour] if colour in COLOUR_NAMES else parse_immediate(args[3]))
            depth = parse_immediate(args[4])
            bytecode.extend(depth.to_bytes(2, 'big'))
        elif opcode == Opcode.EXTRACT:
            # crystal, facet, colour, depth
            bytecode.append(parse_immediate(args[0]))
            bytecode.append(parse_immediate(args[1]))
            colour = args[2].upper()
            bytecode.append(COLOUR_NAMES[colour] if colour in COLOUR_NAMES else parse_immediate(args[2]))
            depth = parse_immediate(args[3])
            bytecode.extend(depth.to_bytes(2, 'big'))
        elif opcode == Opcode.LIGHT_AIM:
            bytecode.append(parse_immediate(args[0]))  # crystal
            bytecode.append(parse_immediate(args[1]))  # facet
        elif opcode == Opcode.LENS_CAPTURE:
            bytecode.append(parse_immediate(args[0]))  # crystal
            bytecode.append(parse_immediate(args[1]))  # facet
            depth = parse_immediate(args[2])
            bytecode.extend(depth.to_bytes(2, 'big'))
        elif opcode == Opcode.LENS_SCAN:
            bytecode.append(parse_immediate(args[0]))  # crystal
        elif opcode in (Opcode.LENS_TO_CHAIN, Opcode.CHAIN_VERIFY):
            pass  # ingen operander
    return bytes(bytecode)

def instruction_size(mnemonic: str, args: list) -> int:
    opcode = Opcode[mnemonic]
    base = 1
    if opcode in (Opcode.LOAD, Opcode.STORE):
        base += 5
    elif opcode == Opcode.MOV:
        base += 3 if args[1].upper().startswith("R") else 6
    elif opcode in (Opcode.ADD, Opcode.SUB, Opcode.MUL, Opcode.DIV):
        base += 2
    elif opcode in (Opcode.ENCODE, Opcode.DECODE):
        base += 1
    elif opcode in (Opcode.JMP, Opcode.CALL):
        base += 4
    elif opcode in (Opcode.JZ, Opcode.JNZ):
        base += 5
    elif opcode == Opcode.SET_COLOR:
        base += 1
    elif opcode == Opcode.SET_POWER:
        base += 1
    elif opcode == Opcode.POSITION:
        base += 6
    elif opcode in (Opcode.LASER_WRITE, Opcode.LASER_READ):
        base += 1
    elif opcode == Opcode.WAIT:
        base += 2
    # v2
    elif opcode in (Opcode.ENCODE_N, Opcode.DECODE_N):
        base += 2  # reg + base
    elif opcode == Opcode.STORE_FACET:
        base += 6  # crystal(1) + facet(1) + colour(1) + depth(2) + reg(1)
    elif opcode == Opcode.LOAD_FACET:
        base += 6  # reg(1) + crystal(1) + facet(1) + colour(1) + depth(2)
    elif opcode == Opcode.EXTRACT:
        base += 5  # crystal(1) + facet(1) + colour(1) + depth(2)
    elif opcode == Opcode.LIGHT_AIM:
        base += 2  # crystal(1) + facet(1)
    elif opcode == Opcode.LENS_CAPTURE:
        base += 4  # crystal(1) + facet(1) + depth(2)
    elif opcode == Opcode.LENS_SCAN:
        base += 1  # crystal(1)
    elif opcode in (Opcode.LENS_TO_CHAIN, Opcode.CHAIN_VERIFY):
        pass  # ingen ekstra bytes
    return base
