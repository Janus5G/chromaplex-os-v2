"""ChromaPlex Python API — skriv og kør krystal-operationer direkte i Python.

I stedet for at skrive CPL eller CPA kan du importere dette modul
og bruge ChromaPlex som et almindeligt Python-bibliotek.

Eksempel:
    from chromaplex_os.api import ChromaPlex

    cx = ChromaPlex(num_crystals=1)
    cx.store(facet=5, colour="GREEN", value=1234567, base=3)
    cx.lens_capture(facet=5)
    wallet = cx.lens_to_chain()
    result = cx.load(facet=5, colour="GREEN")
    print(result)  # 1234567
    print(cx.chain_status())
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from .facet_crystal import FacetAddress, MultiCrystalArray, FACET_BY_ID
from .blockchain_ledger import BlockchainLedger, WalletPayload
from .lens_receiver import LensReceiver, SpectralReading
from .spec import encode_value_raw, decode_value_raw

import hashlib


# Dansk → intern farvemapping
_COLOUR_MAP = {
    "RED": "rød", "GREEN": "grøn", "BLUE": "blå",
    "VIOLET": "violet", "UV": "uv",
    "RØD": "rød", "GRØN": "grøn", "BLÅ": "blå",
}


def _normalise_colour(colour: str) -> str:
    """Konvertér farvenavn til internt format."""
    upper = colour.upper()
    return _COLOUR_MAP.get(upper, colour.lower())


class ChromaPlex:
    """Højniveau Python-API til ChromaPlex krystallagring.

    Brug denne klasse til at skrive Python-scripts der arbejder
    med facetterede krystaller, blockchain og linse-aflæsning.
    """

    def __init__(self, num_crystals: int = 1, max_depth: int = 10) -> None:
        """Opret et ChromaPlex-system.

        Args:
            num_crystals: Antal krystaller (1-100)
            max_depth: Dybdeniveauer pr. facet (1-1000)
        """
        self.crystal_array = MultiCrystalArray(num_crystals, max_depth)
        self.ledger = BlockchainLedger()
        self.lens = LensReceiver()
        self._lens_readings: List[SpectralReading] = []
        self._wallets: List[WalletPayload] = []

    # ----- Skriv og læs -----

    def store(
        self,
        facet: int,
        colour: str = "GREEN",
        value: int = 0,
        base: int = 2,
        crystal: int = 0,
        depth: int = 0,
    ) -> str:
        """Gem en værdi i krystallen og registrér i blockchain.

        Args:
            facet: Facet-ID (0-56)
            colour: Farvekanal (RED, GREEN, BLUE, VIOLET, UV)
            value: Tal-værdien der skal gemmes
            base: Eksponent-base (2, 3, 5, 7, 10...)
            crystal: Krystal-ID (0-99)
            depth: Dybdelag (0-999)

        Returns:
            Adressen der blev skrevet til (f.eks. "C0:F5:grøn:D0")
        """
        cn = _normalise_colour(colour)
        e, rest, base = encode_value_raw(value, base)
        addr = FacetAddress(crystal, facet, cn, depth)

        if not self.ledger.is_address_available(addr.key):
            raise ValueError(
                f"Position {addr.key} er allerede brugt — write-once"
            )

        self.crystal_array.write(crystal, facet, cn, e, rest, base, depth)

        data_hash = hashlib.sha256(
            f"{e}:{rest}:{base}".encode()
        ).hexdigest()
        self.ledger.register_write(addr, data_hash, base)

        return addr.key

    def load(
        self,
        facet: int,
        colour: str = "GREEN",
        crystal: int = 0,
        depth: int = 0,
    ) -> int:
        """Læs en værdi fra krystallen.

        Returns:
            Den rekonstruerede talværdi
        """
        cn = _normalise_colour(colour)
        e, rest, base = self.crystal_array.read(crystal, facet, cn, depth)
        return decode_value_raw(e, rest, base)

    # ----- Linse -----

    def lens_capture(
        self,
        facet: int,
        crystal: int = 0,
        depth: int = 0,
    ) -> Dict[str, int]:
        """Aflæs en facet passivt gennem linsen.

        Returns:
            Dict med farvekanal → værdi for alle kanaler med data
        """
        cryst = self.crystal_array.crystal(crystal)
        reading = self.lens.capture(cryst, facet, depth=depth)
        self._lens_readings.append(reading)
        return reading.channel_values()

    def lens_scan(self, crystal: int = 0) -> int:
        """Scan alle 57 facetter på en krystal.

        Returns:
            Antal facetter med data
        """
        cryst = self.crystal_array.crystal(crystal)
        readings = self.lens.scan_all_facets(cryst)
        self._lens_readings.extend(readings)
        return len(readings)

    def lens_to_chain(self) -> List[Dict]:
        """Send alle linse-aflæsninger til blockchain.

        Returns:
            Liste af wallet-payloads (dict-format)
        """
        payloads = []
        for reading in self._lens_readings:
            if not reading.channels:
                continue
            payload = reading.to_wallet_payload()
            for color, (exp, rest, base) in reading.channels.items():
                addr = FacetAddress(
                    reading.crystal_id, reading.facet_id, color, 0
                )
                if self.ledger.is_address_available(addr.key):
                    dh = hashlib.sha256(
                        f"{exp}:{rest}:{base}".encode()
                    ).hexdigest()
                    self.ledger.register_write(addr, dh, base)
                if self.ledger.is_address_extractable(addr.key):
                    wallet = self.ledger.extract_to_wallet(
                        addr, self.crystal_array
                    )
                    self._wallets.append(wallet)
                    payload["ledger_proof"] = wallet.ledger_proof
            payloads.append(payload)
        self._lens_readings.clear()
        return payloads

    # ----- Udtræk -----

    def extract(
        self,
        facet: int,
        colour: str = "GREEN",
        crystal: int = 0,
        depth: int = 0,
    ) -> WalletPayload:
        """Udtræk data til en wallet-payload og lås positionen.

        Returns:
            WalletPayload med kryptografisk bevis
        """
        cn = _normalise_colour(colour)
        addr = FacetAddress(crystal, facet, cn, depth)
        wallet = self.ledger.extract_to_wallet(addr, self.crystal_array)
        self._wallets.append(wallet)
        return wallet

    # ----- Status -----

    def chain_status(self) -> Dict[str, Any]:
        """Blockchain-status."""
        return self.ledger.status()

    def chain_valid(self) -> bool:
        """Er blockchain-kæden gyldig?"""
        return self.ledger.verify_chain()

    @property
    def wallets(self) -> List[WalletPayload]:
        """Alle udtrukne wallet-payloads."""
        return list(self._wallets)

    def capacity(self) -> Dict[str, Any]:
        """Kapacitetsoverblik."""
        return self.crystal_array.summary()

    def export_wallets_json(self, filepath: str) -> None:
        """Eksportér alle wallets til JSON-fil."""
        data = [w.to_dict() for w in self._wallets]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def export_chain_json(self, filepath: str) -> None:
        """Eksportér hele blockchain-kæden til JSON-fil."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.ledger.export_chain(), f, indent=2, ensure_ascii=False)


def run_python_script(script_path: str) -> None:
    """Kør et Python-script med ChromaPlex API tilgængeligt.

    Scriptet får automatisk en 'cx' variabel der er en ChromaPlex-instans.
    """
    cx = ChromaPlex()
    with open(script_path, "r", encoding="utf-8") as f:
        code = f.read()
    exec(code, {"cx": cx, "ChromaPlex": ChromaPlex, "__name__": "__main__"})
