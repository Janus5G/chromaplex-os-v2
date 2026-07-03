#!/usr/bin/env python3
"""Importér data fra Python til ChromaPlex krystal → blockchain.

Kør:  python examples/python_import.py

Dette script viser hvordan man kan:
  - Importere data fra vilkårlig Python-kilde (fil, API, database)
  - Gemme det i facetterede krystaller
  - Udtrække til blockchain wallets
  - Eksportere wallets som JSON
"""

from chromaplex_os.api import ChromaPlex

# Opret system
cx = ChromaPlex(num_crystals=1)

# === Simulér data fra en ekstern kilde ===
sensor_data = [
    {"id": "temp_01", "value": 2350, "type": "temperatur"},
    {"id": "tryk_01", "value": 101325, "type": "tryk"},
    {"id": "fugt_01", "value": 6500, "type": "fugtighed"},
    {"id": "lys_01", "value": 48000, "type": "lysstyrke"},
    {"id": "co2_01", "value": 415, "type": "co2_ppm"},
]

# Farvemapping: datatype → farvekanal
TYPE_COLOUR = {
    "temperatur": "RED",
    "tryk": "GREEN",
    "fugtighed": "BLUE",
    "lysstyrke": "VIOLET",
    "co2_ppm": "UV",
}

print("=== Importér sensordata til krystal ===\n")

for i, reading in enumerate(sensor_data):
    colour = TYPE_COLOUR[reading["type"]]
    addr = cx.store(
        facet=i,
        colour=colour,
        value=reading["value"],
        base=10,  # base-10 for menneskelæselige tal
    )
    print(f"  {reading['type']:12s} = {reading['value']:>8,} → {addr} ({colour})")

# === Scan med linse og send til blockchain ===
print(f"\n=== Linse-scan og blockchain ===\n")

count = cx.lens_scan()
print(f"  Scannede {count} facetter")

payloads = cx.lens_to_chain()
print(f"  Sendte {len(payloads)} payloads til blockchain")

# === Eksportér ===
cx.export_wallets_json("wallets_export.json")
cx.export_chain_json("chain_export.json")
print(f"\n  Eksporteret til wallets_export.json og chain_export.json")

# === Vis status ===
print(f"\n=== Resultat ===\n")
print(f"  Blockchain blokke: {cx.chain_status()['kædelængde']}")
print(f"  Kæde gyldig: {cx.chain_valid()}")
print(f"  Wallet payloads: {len(cx.wallets)}")

for w in cx.wallets:
    print(f"    {w.source_address}: {w.value:>8,} ({w.base}^{w.exponent}+{w.rest}) ✓")
