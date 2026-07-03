"""Specifikationer for ChromaPlex Assembly (CPA) instruktioner og konstanter.

v2: Udvidet med facet-adressering, base-N, blockchain og linse-opcodes.
"""

from enum import IntEnum

# Krystaldimensioner (legacy voxel-mode)
DIM_X = 1024
DIM_Y = 1024
DIM_Z = 1024

# Facet-konstanter (v2)
NUM_FACETS = 57
MAX_CRYSTALS = 100
MAX_DEPTH = 1000

# Bølgelængder i nanometer
WAVELENGTHS = {
    "UV": 350,
    "VIOLET": 405,
    "BLUE": 473,
    "GREEN": 532,
    "RED": 650,
}
WAVELENGTHS_REVERSE = {v: k for k, v in WAVELENGTHS.items()}
WAVELENGTH_LIST = list(WAVELENGTHS.values())
WAVELENGTH_INDEX = {wl: i for i, wl in enumerate(WAVELENGTH_LIST)}

# Farvekoder
COLOUR_NAMES = {
    "UV": 0,
    "VIOLET": 1,
    "BLUE": 2,
    "GREEN": 3,
    "RED": 4,
}
COLOUR_NAMES_REVERSE = {v: k for k, v in COLOUR_NAMES.items()}

# Opcodes — v1 + v2
class Opcode(IntEnum):
    # === v1 originale ===
    NOP = 0x00
    LOAD = 0x01
    STORE = 0x02
    MOV = 0x03
    ADD = 0x04
    SUB = 0x05
    MUL = 0x06
    DIV = 0x07
    ENCODE = 0x08
    DECODE = 0x09
    JMP = 0x0A
    JZ = 0x0B
    JNZ = 0x0C
    CALL = 0x0D
    RET = 0x0E
    SET_COLOR = 0x0F
    SET_POWER = 0x10
    POSITION = 0x11
    LASER_WRITE = 0x12
    LASER_READ = 0x13
    WAIT = 0x14
    # === v2 nye ===
    ENCODE_N = 0x20       # encode med vilkårlig base
    DECODE_N = 0x21       # decode med vilkårlig base
    STORE_FACET = 0x30    # skriv til facet + blockchain
    LOAD_FACET = 0x31     # læs fra facet
    EXTRACT = 0x32        # udtræk til wallet, lås position
    LIGHT_AIM = 0x33      # ret lyskilde mod facet
    LENS_CAPTURE = 0x34   # aflæs facet gennem linse
    LENS_SCAN = 0x35      # scan alle facetter
    LENS_TO_CHAIN = 0x36  # send linse-data til blockchain
    CHAIN_VERIFY = 0x37   # verificér blockchain
    HALT = 0xFF

NUM_REGISTERS = 8
MAX_RAW_VALUE = 2**32 - 1


def encode_value(value: int, base: int = 2) -> int:
    """Kod et positivt heltal til pakket format.

    v2: Understøtter vilkårlig base (2, 3, 5, 7, 10...).
    Format: (base << 28) | (exponent << 20) | (remainder & 0xFFFFF)
    Legacy base-2: (exponent << 24) | (remainder & 0xFFFFFF)
    """
    if value < 0:
        raise ValueError("Kun ikke-negative tal kan kodes.")
    if value == 0:
        return 0
    if base == 2:
        # Legacy format for bagudkompatibilitet
        e = value.bit_length() - 1
        remainder = value - (1 << e)
        packed = (e << 24) | (remainder & 0xFFFFFF)
        return packed
    else:
        # v2 base-N format
        e = 0
        while base ** (e + 1) <= value:
            e += 1
        remainder = value - base ** e
        packed = (base << 28) | (e << 20) | (remainder & 0xFFFFF)
        return packed


def decode_value(packed: int, base: int = 2) -> int:
    """Afkod et pakket tal tilbage til original værdi.

    v2: Understøtter vilkårlig base.
    """
    if packed == 0:
        return 0
    if base == 2:
        # Legacy format
        e = (packed >> 24) & 0xFF
        remainder = packed & 0xFFFFFF
        if e == 0 and remainder == 0:
            return 0
        return (1 << e) + remainder
    else:
        # v2 base-N format
        stored_base = (packed >> 28) & 0xF
        if stored_base > 0:
            base = stored_base
        e = (packed >> 20) & 0xFF
        remainder = packed & 0xFFFFF
        return base ** e + remainder


def encode_value_raw(value: int, base: int = 2) -> tuple:
    """Returnér (exponent, rest, base) uden pakning — til facet-lagring."""
    if value < 0:
        raise ValueError("Kun ikke-negative tal kan kodes.")
    if value == 0:
        return (0, 0, base)
    if base < 2:
        raise ValueError(f"Base skal være mindst 2, fik {base}")
    e = 0
    while base ** (e + 1) <= value:
        e += 1
    rest = value - base ** e
    return (e, rest, base)


def decode_value_raw(e: int, rest: int, base: int = 2) -> int:
    """Rekonstruér tal fra (exponent, rest, base)."""
    if base < 2:
        raise ValueError(f"Base skal være mindst 2, fik {base}")
    return base ** e + rest
