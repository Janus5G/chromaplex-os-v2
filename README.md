# ChromaPlex OS v2 — Faceted Crystal Storage with Blockchain

A programming language and software stack for optical crystal data storage.
Store data as light refracted through a 57-facet brilliant-cut crystal,
read it passively with a lens, and send it to a blockchain wallet.

**[Live Demo](https://janus5g.github.io/chromaplex-os-v2/demo/)** · **[Live Blockchain Wallet](https://chromaplex-wallet-sgm.caffeine.xyz/)** · **[Original v1](https://github.com/Janus5G/chromaplex-os)** · **[Desktop IDE](https://github.com/Janus5G/Cplex)** · **[Compiler](https://github.com/Janus5G/chromaplex-os-compiler)**

---

## What's new in v2?

| Feature | v1 | v2 |
|---|---|---|
| Addressing | Voxel (x,y,z) | 57-facet crystal × 5 colors × depth |
| Exponent base | Only ^2 | Any ^N (2, 3, 5, 7, 10...) |
| Data integrity | None | Write-once blockchain with SHA-256 |
| Data transfer | None | Wallet extraction with cryptographic proof |
| Light source | Implicit | Explicit control (source moves, crystal stays) |
| Crystals | 1 | Multi-crystal with combinatorial capacity |
| Lens readout | None | Passive readout via Snell's law refraction |
| Python API | None | `from chromaplex_os.api import ChromaPlex` |

---

## Quick start

```bash
git clone https://github.com/Janus5G/chromaplex-os-v2.git
cd chromaplex-os-v2
pip install -e .
pip install pytest
python -m pytest tests/ -v        # 72 tests pass
python examples/python_demo.py    # Full pipeline demo
```

---

## Program in Python (3 lines to store data on crystal → blockchain)

```python
from chromaplex_os.api import ChromaPlex

cx = ChromaPlex()
cx.store(facet=5, colour="GREEN", value=1234567, base=3)
cx.lens_capture(facet=5)
cx.lens_to_chain()

result = cx.load(facet=5, colour="GREEN")
print(result)  # 1234567
print(cx.chain_valid())  # True
```

Run it: `python examples/python_demo.py`

---

## Program in CPL (the ChromaPlex language)

```
// Store data in crystal facet 5, green channel
var data = 1234567;
store data at facet(0, 5) colour GREEN;

// Lens reads passively — no heat, no wear
lens_capture facet(0, 5);

// Send to blockchain wallet
lens_to_chain;

// Read back and verify
load result from facet(0, 5) colour GREEN;
print result;  // 1234567
```

---

## How it works

```
[Laser] → [Facet] → [Crystal] → [Refracted light] → [Lens] → [Color data] → [Blockchain]
```

The crystal sits still. The light source moves. Each of the 57 facets
refracts light at a unique angle — producing a unique color signature
that IS the data. The lens on the opposite side captures the spectrum.
No writing to the crystal = no heat, no wear.

### The 57-facet model

A brilliant-cut diamond shape with 57 facets:

| Group | Count | θ (polar) |
|---|---|---|
| Table (top) | 1 | 0° |
| Crown star | 8 | 15° |
| Crown main | 8 | 34.5° |
| Upper girdle | 16 | 42° |
| Lower girdle | 16 | 138° |
| Pavilion | 8 | 155° |
| **Total** | **57** | |

With 5 color channels (Red, Green, Blue, Violet, UV) and 10 depth levels:
- 1 crystal: 2,850 addresses
- 2 crystals: 8,122,500 addresses
- 3 crystals: 23,149,125,000 addresses

---

## Blockchain: write-once ledger

Every write to a crystal position is recorded in a SHA-256 chain.
Once data is extracted to a wallet, the position is permanently locked.

```python
cx = ChromaPlex()

# Write — position is now registered
cx.store(facet=5, colour="GREEN", value=42)

# Extract — position is permanently locked
wallet = cx.extract(facet=5, colour="GREEN")
print(wallet.verify())  # True

# Try to write again — REJECTED
cx.store(facet=5, colour="GREEN", value=99)  # ValueError: write-once
```

The live wallet runs on Internet Computer:
**[chromaplex-wallet-sgm.caffeine.xyz](https://chromaplex-wallet-sgm.caffeine.xyz/)**

---

## Lens receiver: passive readout

The lens model uses Snell's law with realistic refractive indices
for fused silica:

| Channel | Wavelength | Refractive index |
|---|---|---|
| Red | ~630 nm | 1.4580 |
| Green | ~530 nm | 1.4613 |
| Blue | ~470 nm | 1.4650 |
| Violet | ~410 nm | 1.4701 |
| UV | ~350 nm | 1.4760 |

```python
cx = ChromaPlex()
cx.store(facet=10, colour="RED", value=500)
cx.store(facet=10, colour="GREEN", value=800)

# Lens reads all channels at once
colors = cx.lens_capture(facet=10)
print(colors)  # {'rød': 500, 'grøn': 800}

# Scan all 57 facets
count = cx.lens_scan()
print(f"Found data on {count} facets")
```

---

## Bytecode VM

ChromaPlex compiles CPL → CPA assembly → bytecode. The VM executes
real opcodes, not interpreted strings.

### v2 opcodes

| Opcode | Hex | Description |
|---|---|---|
| ENCODE_N | 0x20 | Encode with arbitrary base (^N) |
| DECODE_N | 0x21 | Decode with arbitrary base |
| STORE_FACET | 0x30 | Write to facet + blockchain |
| LOAD_FACET | 0x31 | Read from facet |
| EXTRACT | 0x32 | Extract to wallet, lock position |
| LIGHT_AIM | 0x33 | Aim light source at facet |
| LENS_CAPTURE | 0x34 | Read facet through lens |
| LENS_SCAN | 0x35 | Scan all 57 facets |
| LENS_TO_CHAIN | 0x36 | Send lens readings to blockchain |
| CHAIN_VERIFY | 0x37 | Verify blockchain integrity |

All v1 opcodes (0x00–0x14) remain fully compatible.

---

## Tests

```
$ python -m pytest tests/ -v
tests/test_assembler.py            2 passed   (v1 bytecode)
tests/test_python_api.py          11 passed   (Python API)
tests/test_v2_core.py             38 passed   (facets, blockchain, lens, base-N)
tests/test_v2_integration.py      21 passed   (bytecode VM integration)
============================== 72 passed ==============================
```

---

## Project structure

```
chromaplex-os-v2/
├── chromaplex_os/
│   ├── __init__.py
│   ├── spec.py              # Opcodes, constants, base-N encode/decode
│   ├── vm.py                # Bytecode VM (v1 + v2 instructions)
│   ├── assembler.py         # CPA → bytecode
│   ├── compiler.py          # CPL → CPA
│   ├── storage.py           # Legacy voxel storage
│   ├── hardware.py          # Laser control simulation
│   ├── api.py               # Python API (ChromaPlex class)
│   ├── facet_crystal.py     # 57-facet model + light source + multi-crystal
│   ├── blockchain_ledger.py # Write-once blockchain + wallet extraction
│   ├── lens_receiver.py     # Passive lens readout with Snell's law
│   ├── cli.py               # Command-line interface
│   ├── visual_demo.py       # Visualization
│   └── visualization_viewer.py
├── examples/
│   ├── python_demo.py       # Full Python pipeline demo
│   ├── python_import.py     # Import external data into crystal
│   ├── hello.cpl            # Simple CPL program
│   └── fibonacci.cpl
├── tests/
│   ├── test_assembler.py    # v1 assembler tests
│   ├── test_v2_integration.py  # v2 bytecode integration tests
│   └── test_python_api.py   # Python API tests
├── docs/
│   └── ...
├── setup.py
└── README.md
```

---

## CLI

```bash
# Compile and run CPL
chromaplex compile program.cpl -o program.bin
chromaplex run program.bin

# Run from source
chromaplex run --source program.cpl

# Run Python script with ChromaPlex API
chromaplex python script.py
```

---

## Related repositories

- **[chromaplex-os](https://github.com/Janus5G/chromaplex-os)** — Original v1 language and voxel model
- **[chromaplex-os-compiler](https://github.com/Janus5G/chromaplex-os-compiler)** — Compiler toolchain with browser 3D simulator
- **[Cplex](https://github.com/Janus5G/Cplex)** — Rust/Slint desktop IDE
- **[ChromaPlex Wallet](https://chromaplex-wallet-sgm.caffeine.xyz/)** — Live blockchain wallet on Internet Computer

---

## License

MIT — free to use, modify, and sell.
