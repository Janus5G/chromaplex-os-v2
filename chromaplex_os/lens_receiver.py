"""Linsemodtager til ChromaPlex v2.

Modellerer en linse på den modsatte side af krystallen fra laseren.
Linsen opfanger det refrakterede lys og dekoder farvespektret til data.

Flow:
  [Laser] → [Facet] → [Krystal] → [Refrakteret lys] → [Linse] → [Farvedata] → [Blockchain]

Fordelen: krystallen skrives aldrig til. Den er et passivt optisk element.
Ingen varmeudvikling, ingen slitage, uendelig holdbarhed.
Krystallens facetter og indre struktur ER dataen — slebet ind permanent.

Linsemodellen understøtter:
  - Enkelt-facet aflæsning (1 laser → 1 facet → 1 farvesæt)
  - Multi-facet scanning (laser sweeper hen over facetter)
  - Spektraldekomponering (split refrakteret lys i RGB+Violet+UV)
  - Direkte pipeline til blockchain-wallet
"""

from __future__ import annotations

import hashlib
import math
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .facet_crystal import (
    BRILLANT_FACETS,
    COLORS,
    FACET_BY_ID,
    Facet,
    FacetAddress,
    FacetCrystal,
    LightSource,
    MultiCrystalArray,
)


# ---------------------------------------------------------------------------
# Spektraldekomponering — hvad linsen ser
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SpectralReading:
    """Én aflæsning fra linsen: hvad der kom ud på den anden side."""
    crystal_id: int
    facet_id: int
    facet_name: str
    theta_in: float       # indgangsvinkel
    phi_in: float         # indgangs-azimut
    channels: Dict[str, Tuple[int, int, int]]  # farve -> (exp, rest, base)
    timestamp: float

    @property
    def address(self) -> str:
        """Generér ChromaPlex-adresse for denne aflæsning."""
        colors = list(self.channels.keys())
        primary = colors[0] if colors else "grøn"
        return f"C{self.crystal_id}:F{self.facet_id}:{primary}:D0"

    @property
    def total_value(self) -> int:
        """Samlet talværdi fra alle kanaler."""
        total = 0
        for color, (exp, rest, base) in self.channels.items():
            total += base ** exp + rest
        return total

    def channel_values(self) -> Dict[str, int]:
        """Rekonstruerede værdier pr. kanal."""
        return {
            color: base ** exp + rest
            for color, (exp, rest, base) in self.channels.items()
        }

    def to_wallet_payload(self) -> Dict[str, Any]:
        """Konvertér til WalletPayload-format klar til blockchain."""
        values = self.channel_values()
        primary_color = list(self.channels.keys())[0]
        exp, rest, base = self.channels[primary_color]
        value = base ** exp + rest

        source_address = f"C{self.crystal_id}:F{self.facet_id}:{primary_color}:D0"

        # Beregn extraction_hash (matcher ChromaPlex-formatet)
        raw = f"{source_address}:{value}:{base}:{exp}:{rest}"
        extraction_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        # Payload-ID fra tidsstempel + adresse
        pid_raw = f"{source_address}:{extraction_hash}:{self.timestamp}"
        payload_id = hashlib.sha256(pid_raw.encode("utf-8")).hexdigest()[:16]

        return {
            "payload_id": payload_id,
            "source_address": source_address,
            "value": value,
            "representation": f"{base}^{exp} + {rest}",
            "extraction_hash": extraction_hash,
            "ledger_proof": [],  # udfyldes af blockchain-systemet
            "timestamp": self.timestamp,
            "all_channels": {
                color: {
                    "value": base ** e + r,
                    "representation": f"{b}^{e} + {r}",
                }
                for color, (e, r, b) in self.channels.items()
            },
        }


# ---------------------------------------------------------------------------
# Refraktionsmodel — hvad sker med lyset i krystallen
# ---------------------------------------------------------------------------

# Refraktive indekser for simulerede farvekanaler i smeltet silica
# (baseret på Sellmeier-ligningen, forenklet til simulering)
REFRACTIVE_INDICES = {
    "rød": 1.4580,     # ~630 nm
    "grøn": 1.4613,    # ~530 nm
    "blå": 1.4650,     # ~470 nm
    "violet": 1.4701,  # ~410 nm
    "uv": 1.4760,      # ~350 nm
}


def _compute_refraction(
    theta_in: float,
    n1: float = 1.0,   # luft
    n2: float = 1.46,  # smeltet silica
) -> float:
    """Beregn udgangsvinklen via Snell's lov."""
    theta_rad = math.radians(theta_in)
    sin_out = (n1 / n2) * math.sin(theta_rad)
    # Total intern reflektion
    if abs(sin_out) > 1.0:
        return -1.0  # reflekteret, ingen gennemgang
    return math.degrees(math.asin(sin_out))


def _spectral_dispersion(theta_in: float) -> Dict[str, float]:
    """Beregn udgangsvinkler for alle farvekanaler.

    Forskellige bølgelængder refrakterer med forskellige vinkler
    pga. dispersion i krystallen. Det er det der gør at en prisme
    splitter hvidt lys i regnbuens farver.
    """
    result = {}
    for color, n in REFRACTIVE_INDICES.items():
        theta_out = _compute_refraction(theta_in, n2=n)
        result[color] = theta_out
    return result


# ---------------------------------------------------------------------------
# Linsen — opfanger refrakteret lys
# ---------------------------------------------------------------------------

class LensReceiver:
    """Linse på den modsatte side af krystallen.

    Opfanger det refrakterede lys og dekoder det til farvedata.
    Kræver ingen skrivning til krystallen — rent passiv aflæsning.

    Brug:
        lens = LensReceiver()
        reading = lens.capture(crystal, facet_id=5)
        payload = reading.to_wallet_payload()  # klar til blockchain
    """

    def __init__(self, sensitivity: float = 1.0) -> None:
        """Opret linsemodtager.

        Args:
            sensitivity: Følsomhed 0.0-1.0 (påvirker støjmodel)
        """
        self.sensitivity = max(0.0, min(1.0, sensitivity))
        self._readings: List[SpectralReading] = []

    def capture(
        self,
        crystal: FacetCrystal,
        facet_id: int,
        colors: List[str] | None = None,
        depth: int = 0,
    ) -> SpectralReading:
        """Aflæs en enkelt facet gennem linsen.

        Laseren rammer facetten, lyset går igennem krystallen,
        linsen opfanger det refrakterede spektrum.

        Args:
            crystal: Krystallen der aflæses
            facet_id: Hvilken facet laseren rammer
            colors: Hvilke farvekanaler der aflæses (None = alle)
            depth: Dybdelag

        Returns:
            SpectralReading med alle aflæste farvekanaler
        """
        if facet_id < 0 or facet_id >= 57:
            raise ValueError(f"Facet-ID {facet_id} udenfor rækkevidde (0-56)")

        facet = FACET_BY_ID[facet_id]
        if colors is None:
            colors = list(COLORS)

        # Ret lyskilden mod facetten
        crystal.light.aim_at_facet(facet)

        # Beregn refraktion og dispersion
        dispersions = _spectral_dispersion(facet.theta)

        # Aflæs data fra krystallen for hver farvekanal
        channels: Dict[str, Tuple[int, int, int]] = {}
        for color in colors:
            if crystal.is_written(facet_id, color, depth):
                exp, rest, base = crystal.read(facet_id, color, depth)
                channels[color] = (exp, rest, base)

        reading = SpectralReading(
            crystal_id=crystal.crystal_id,
            facet_id=facet_id,
            facet_name=facet.name,
            theta_in=facet.theta,
            phi_in=facet.phi,
            channels=channels,
            timestamp=time.time(),
        )
        self._readings.append(reading)
        return reading

    def scan_all_facets(
        self,
        crystal: FacetCrystal,
        colors: List[str] | None = None,
        depth: int = 0,
    ) -> List[SpectralReading]:
        """Scan alle 57 facetter sekventielt.

        Returnerer kun facetter der indeholder data.
        """
        readings = []
        for facet in BRILLANT_FACETS:
            reading = self.capture(crystal, facet.id, colors, depth)
            if reading.channels:  # kun facetter med data
                readings.append(reading)
        return readings

    def scan_to_wallet_payloads(
        self,
        crystal: FacetCrystal,
        colors: List[str] | None = None,
        depth: int = 0,
    ) -> List[Dict[str, Any]]:
        """Scan alle facetter og konvertér direkte til wallet-payloads.

        Dette er den primære pipeline:
        Laser → Krystal → Linse → Wallet-payloads → Blockchain
        """
        readings = self.scan_all_facets(crystal, colors, depth)
        return [r.to_wallet_payload() for r in readings]

    def capture_multi_crystal(
        self,
        array: MultiCrystalArray,
        facet_id: int,
        colors: List[str] | None = None,
        depth: int = 0,
    ) -> List[SpectralReading]:
        """Aflæs samme facet på alle krystaller i et array."""
        readings = []
        for crystal in array.crystals:
            reading = self.capture(crystal, facet_id, colors, depth)
            if reading.channels:
                readings.append(reading)
        return readings

    @property
    def reading_count(self) -> int:
        return len(self._readings)

    @property
    def readings(self) -> List[SpectralReading]:
        return list(self._readings)

    def clear(self) -> None:
        """Nulstil aflæsningshistorik."""
        self._readings.clear()
