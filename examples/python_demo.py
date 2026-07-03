#!/usr/bin/env python3
"""ChromaPlex Python Demo — fuld pipeline i rent Python.

Kør:  python examples/python_demo.py

Demonstrerer:
  1. Gem data i facetteret krystal med farvekanal
  2. Linse-aflæsning (passiv, ingen varme)
  3. Udtræk til blockchain wallet
  4. Verificér kædens integritet
"""

from chromaplex_os.api import ChromaPlex

# Opret system med 2 krystaller
cx = ChromaPlex(num_crystals=2)

# === Gem data ===
print("=== Gem data i krystaller ===")

addr1 = cx.store(facet=5, colour="GREEN", value=1234567, base=3)
print(f"  Gemt 1234567 (base 3) → {addr1}")

addr2 = cx.store(facet=10, colour="RED", value=42, base=2, crystal=1)
print(f"  Gemt 42 (base 2) → {addr2}")

addr3 = cx.store(facet=20, colour="BLUE", value=999999, base=7)
print(f"  Gemt 999999 (base 7) → {addr3}")

# === Læs data ===
print("\n=== Læs data tilbage ===")

val1 = cx.load(facet=5, colour="GREEN")
print(f"  Facet 5, grøn: {val1}")

val2 = cx.load(facet=10, colour="RED", crystal=1)
print(f"  Facet 10, rød (krystal 1): {val2}")

# === Linse-aflæsning ===
print("\n=== Linse-aflæsning (passiv) ===")

colours = cx.lens_capture(facet=5)
print(f"  Facet 5 farver: {colours}")

scan_count = cx.lens_scan()
print(f"  Scan fandt {scan_count} facetter med data")

# === Send til blockchain ===
print("\n=== Blockchain wallet ===")

payloads = cx.lens_to_chain()
print(f"  {len(payloads)} payloads sendt til chain")

for p in payloads:
    print(f"    {p['source_address']}: {p['value']} ({p['representation']})")

# === Udtræk direkte ===
print("\n=== Direkte udtræk ===")

wallet = cx.extract(facet=10, colour="RED", crystal=1)
print(f"  Wallet ID: {wallet.payload_id}")
print(f"  Værdi: {wallet.value}")
print(f"  Bevis: {len(wallet.ledger_proof)} blokke")
print(f"  Verificeret: {wallet.verify()}")

# === Status ===
print("\n=== Blockchain status ===")
status = cx.chain_status()
for k, v in status.items():
    print(f"  {k}: {v}")

print(f"\n  Kæde gyldig: {cx.chain_valid()}")
print(f"  Wallets: {len(cx.wallets)}")
print(f"  Kapacitet: {cx.capacity()['kombinatorisk_kapacitet']:,} adresser")

print("\nDone! ✓")
