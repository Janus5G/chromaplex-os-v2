"""Blockchain-ledger til ChromaPlex.

Implementerer write-once-semantik med kryptografisk kæde:
  - Hver skrivning hasher den forrige entry (blockchain-princip)
  - Brugte positioner låses permanent — lyskilde og facet kan ikke genbruges
  - Udtræk af data genererer en wallet-kompatibel payload

Sikkerhedsmodel:
  - Positionslåsning er softwarestyret for både lyskilde og krystalposition
  - Ingen fysisk destruktion nødvendig — garantien er kryptografisk
  - Udtræk markerer positionen som "forbrugt" med en signeret hash
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .facet_crystal import FacetAddress, MultiCrystalArray


# ---------------------------------------------------------------------------
# Blockchain entry
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LedgerEntry:
    """En enkelt entry i blockchain-ledgeren."""
    index: int
    timestamp: float
    address: str              # FacetAddress.key
    data_hash: str            # SHA-256 af de gemte data
    operation: str            # "WRITE" eller "EXTRACT"
    previous_hash: str        # Hash af forrige entry
    base: int                 # Eksponent-base (2, 3, N...)
    crystal_id: int
    facet_id: int
    color: str
    depth: int

    @property
    def block_hash(self) -> str:
        """Beregn denne entrys hash."""
        content = (
            f"{self.index}:{self.timestamp}:{self.address}:"
            f"{self.data_hash}:{self.operation}:{self.previous_hash}:"
            f"{self.base}:{self.crystal_id}:{self.facet_id}:"
            f"{self.color}:{self.depth}"
        )
        return hashlib.sha256(content.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Wallet payload — til udtræk og overførsel
# ---------------------------------------------------------------------------

@dataclass
class WalletPayload:
    """Data pakket til overførsel via blockchain wallet.

    Indeholder alt nødvendigt for at verificere og rekonstruere data
    fra en krystalposition der nu er låst.
    """
    payload_id: str
    source_address: str
    value: int
    exponent: int
    rest: int
    base: int
    extraction_hash: str
    ledger_proof: List[str]   # kæde af block-hashes som bevis
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "payload_id": self.payload_id,
            "source_address": self.source_address,
            "value": self.value,
            "representation": f"{self.base}^{self.exponent} + {self.rest}",
            "extraction_hash": self.extraction_hash,
            "ledger_proof": self.ledger_proof,
            "timestamp": self.timestamp,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    def verify(self) -> bool:
        """Verificér at payload er konsistent."""
        expected = self.base ** self.exponent + self.rest
        if expected != self.value:
            return False
        # Verificér hash
        raw = f"{self.source_address}:{self.value}:{self.base}:{self.exponent}:{self.rest}"
        expected_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return self.extraction_hash == expected_hash


# ---------------------------------------------------------------------------
# Blockchain ledger
# ---------------------------------------------------------------------------

class BlockchainLedger:
    """Write-once blockchain ledger for krystalpositioner.

    Regler:
      1. En position kan kun skrives til én gang (WRITE)
      2. Data kan udtrækkes én gang (EXTRACT) → genererer WalletPayload
      3. Efter udtræk er positionen permanent låst
      4. Lyskilden afvises fra at ramme låste positioner
      5. Hver operation kædes kryptografisk til den forrige
    """

    GENESIS_HASH = "0" * 64  # Genesis-blok hash

    def __init__(self) -> None:
        self._chain: List[LedgerEntry] = []
        self._locked_addresses: set[str] = set()    # skrevet til
        self._extracted_addresses: set[str] = set()  # udtrukt og låst
        self._wallets: Dict[str, WalletPayload] = {}

    @property
    def chain_length(self) -> int:
        return len(self._chain)

    @property
    def last_hash(self) -> str:
        if not self._chain:
            return self.GENESIS_HASH
        return self._chain[-1].block_hash

    def is_address_available(self, address: str) -> bool:
        """Tjek om en adresse er ledig til skrivning."""
        return address not in self._locked_addresses

    def is_address_extractable(self, address: str) -> bool:
        """Tjek om data på en adresse kan udtrækkes."""
        return (
            address in self._locked_addresses
            and address not in self._extracted_addresses
        )

    def is_address_spent(self, address: str) -> bool:
        """Tjek om en adresse er permanent forbrugt."""
        return address in self._extracted_addresses

    def register_write(self, addr: FacetAddress, data_hash: str, base: int = 2) -> LedgerEntry:
        """Registrér en skrivning i ledgeren.

        Raises:
            ValueError: Hvis adressen allerede er brugt.
        """
        if not self.is_address_available(addr.key):
            raise ValueError(
                f"Adresse {addr.key} er allerede brugt — "
                f"write-once-princippet forhindrer genskrivning"
            )

        entry = LedgerEntry(
            index=len(self._chain),
            timestamp=time.time(),
            address=addr.key,
            data_hash=data_hash,
            operation="WRITE",
            previous_hash=self.last_hash,
            base=base,
            crystal_id=addr.crystal_id,
            facet_id=addr.facet_id,
            color=addr.color,
            depth=addr.depth,
        )
        self._chain.append(entry)
        self._locked_addresses.add(addr.key)
        return entry

    def extract_to_wallet(
        self,
        addr: FacetAddress,
        crystal_array: MultiCrystalArray,
    ) -> WalletPayload:
        """Udtræk data fra en krystalposition til en wallet-payload.

        1. Læser data fra krystallen
        2. Opretter wallet-payload med bevis
        3. Markerer positionen som permanent forbrugt
        4. Låser lyskilden fra den position

        Raises:
            ValueError: Hvis data ikke kan udtrækkes.
        """
        if not self.is_address_extractable(addr.key):
            if self.is_address_spent(addr.key):
                raise ValueError(
                    f"Adresse {addr.key} er allerede udtrukt og permanent låst"
                )
            raise ValueError(
                f"Adresse {addr.key} har ingen data at udtrække"
            )

        # Læs data fra krystallen
        exp, rest, base = crystal_array.read(
            addr.crystal_id, addr.facet_id, addr.color, addr.depth
        )
        value = base**exp + rest

        # Opret extraction hash
        raw = f"{addr.key}:{value}:{base}:{exp}:{rest}"
        extraction_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        # Saml bevis-kæde (alle block-hashes for denne adresse)
        proof = [
            e.block_hash for e in self._chain if e.address == addr.key
        ]

        # Registrér udtræk i ledgeren
        entry = LedgerEntry(
            index=len(self._chain),
            timestamp=time.time(),
            address=addr.key,
            data_hash=extraction_hash,
            operation="EXTRACT",
            previous_hash=self.last_hash,
            base=base,
            crystal_id=addr.crystal_id,
            facet_id=addr.facet_id,
            color=addr.color,
            depth=addr.depth,
        )
        self._chain.append(entry)
        self._extracted_addresses.add(addr.key)
        proof.append(entry.block_hash)

        # Opret payload-id
        payload_id = hashlib.sha256(
            f"{addr.key}:{extraction_hash}:{entry.timestamp}".encode()
        ).hexdigest()[:16]

        wallet = WalletPayload(
            payload_id=payload_id,
            source_address=addr.key,
            value=value,
            exponent=exp,
            rest=rest,
            base=base,
            extraction_hash=extraction_hash,
            ledger_proof=proof,
            timestamp=entry.timestamp,
        )
        self._wallets[payload_id] = wallet
        return wallet

    def verify_chain(self) -> bool:
        """Verificér hele blockchain-kædens integritet."""
        if not self._chain:
            return True
        if self._chain[0].previous_hash != self.GENESIS_HASH:
            return False
        for i in range(1, len(self._chain)):
            if self._chain[i].previous_hash != self._chain[i - 1].block_hash:
                return False
        return True

    def get_wallet(self, payload_id: str) -> Optional[WalletPayload]:
        """Hent en wallet-payload via ID."""
        return self._wallets.get(payload_id)

    def status(self) -> Dict[str, Any]:
        """Overblik over ledger-status."""
        return {
            "kædelængde": self.chain_length,
            "skrevne_adresser": len(self._locked_addresses),
            "udtrukne_adresser": len(self._extracted_addresses),
            "ledige_wallets": len(self._wallets),
            "kæde_gyldig": self.verify_chain(),
        }

    def export_chain(self) -> List[Dict[str, Any]]:
        """Eksportér hele kæden som JSON-kompatibel liste."""
        return [
            {
                "index": e.index,
                "timestamp": e.timestamp,
                "address": e.address,
                "operation": e.operation,
                "data_hash": e.data_hash,
                "block_hash": e.block_hash,
                "previous_hash": e.previous_hash,
                "base": e.base,
            }
            for e in self._chain
        ]
