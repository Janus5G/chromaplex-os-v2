"""Facetteret krystalmodel til ChromaPlex v2.

Modellerer en brillantslebet krystal med 57 facetter (uden culet).
Lyskilden flyttes — krystallen forbliver stationær.

Hver facet har en unik vinkel (theta, phi) i forhold til krystallens
optiske akse, hvilket giver diskret adressering frem for analogt.

Multi-krystal-kombinatorik mangedobler adresserummet:
  1 krystal:  57 × farver × dybder
  2 krystaller: kombination² 
  N krystaller: kombination^N
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .spec import encode_value_raw, decode_value_raw


# ---------------------------------------------------------------------------
# Facetdefinitioner for brillantsleben diamant (57 facetter)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Facet:
    """En enkelt facet med unik vinkel i krystallen."""
    id: int
    name: str
    theta: float   # polær vinkel i grader fra optisk akse
    phi: float     # azimut vinkel i grader
    group: str     # krone, pavillon, bord, etc.


def _build_brillant_facets() -> List[Facet]:
    """Generér 57 facetter for en standard brillantslebet diamant.

    Grupper:
      - Bord (table):           1 facet
      - Krone-hovedfacetter:    8 facetter (star facets)
      - Krone-bifacetter:       8 facetter (bezel/kite facets)
      - Øvre bælte (upper girdle): 16 facetter
      - Nedre bælte (lower girdle): 16 facetter
      - Pavillon-hovedfacetter: 8 facetter
    Total: 1 + 8 + 8 + 16 + 16 + 8 = 57
    """
    facets: List[Facet] = []
    fid = 0

    # 1: Bord — flad top, theta ≈ 0°
    facets.append(Facet(fid, "bord", theta=0.0, phi=0.0, group="bord"))
    fid += 1

    # 8: Krone-stjernefacetter — lav vinkel, jævnt fordelt
    for i in range(8):
        phi = i * 45.0
        facets.append(Facet(fid, f"krone_stjerne_{i}", theta=15.0, phi=phi, group="krone_stjerne"))
        fid += 1

    # 8: Krone-hovedfacetter (bezel/kite) — middel vinkel
    for i in range(8):
        phi = i * 45.0 + 22.5
        facets.append(Facet(fid, f"krone_hoved_{i}", theta=34.5, phi=phi, group="krone_hoved"))
        fid += 1

    # 16: Øvre bæltefacetter
    for i in range(16):
        phi = i * 22.5
        facets.append(Facet(fid, f"øvre_bælte_{i}", theta=42.0, phi=phi, group="øvre_bælte"))
        fid += 1

    # 16: Nedre bæltefacetter
    for i in range(16):
        phi = i * 22.5 + 11.25
        facets.append(Facet(fid, f"nedre_bælte_{i}", theta=138.0, phi=phi, group="nedre_bælte"))
        fid += 1

    # 8: Pavillon-hovedfacetter — stejl vinkel
    for i in range(8):
        phi = i * 45.0
        facets.append(Facet(fid, f"pavillon_{i}", theta=155.0, phi=phi, group="pavillon"))
        fid += 1

    assert len(facets) == 57, f"Forventede 57 facetter, fik {len(facets)}"
    return facets


BRILLANT_FACETS: List[Facet] = _build_brillant_facets()
FACET_BY_ID: Dict[int, Facet] = {f.id: f for f in BRILLANT_FACETS}
FACET_BY_NAME: Dict[str, Facet] = {f.name: f for f in BRILLANT_FACETS}

# Gyldige farvekanaler
COLORS = {"rød", "grøn", "blå", "violet", "uv"}


# ---------------------------------------------------------------------------
# Lyskildeposition — styrer hvilken facet der rammes
# ---------------------------------------------------------------------------

@dataclass
class LightSource:
    """Repræsenterer en bevægelig lyskilde der rammer krystallen.

    I stedet for at flytte krystallen flytter vi lyskilden.
    Positionen bestemmer hvilken facet der aktiveres.
    """
    theta: float = 0.0
    phi: float = 0.0
    wavelength: str = "grøn"     # aktiv farvekanal
    intensity: float = 1.0

    def aim_at_facet(self, facet: Facet) -> None:
        """Ret lyskilden mod en specifik facet."""
        self.theta = facet.theta
        self.phi = facet.phi

    def find_nearest_facet(self, facets: List[Facet] = BRILLANT_FACETS) -> Facet:
        """Find den facet der er nærmest lysets aktuelle position."""
        best = facets[0]
        best_dist = float("inf")
        for f in facets:
            # Sfærisk afstand (approksimeret)
            dt = math.radians(self.theta - f.theta)
            dp = math.radians(self.phi - f.phi)
            dist = math.sqrt(dt * dt + dp * dp)
            if dist < best_dist:
                best_dist = dist
                best = f
        return best


# ---------------------------------------------------------------------------
# Facetteret krystal med dybdelag
# ---------------------------------------------------------------------------

@dataclass
class FacetAddress:
    """Fuld adresse i en facetteret krystal."""
    crystal_id: int
    facet_id: int
    color: str
    depth: int = 0

    def __post_init__(self):
        if self.color not in COLORS:
            raise ValueError(f"Ukendt farve: {self.color}")
        if self.facet_id < 0 or self.facet_id >= 57:
            raise ValueError(f"Facet-ID skal være 0-56, fik {self.facet_id}")
        if self.depth < 0:
            raise ValueError("Dybde kan ikke være negativ")

    @property
    def key(self) -> str:
        """Unik nøgle til blockchain-ledger."""
        return f"C{self.crystal_id}:F{self.facet_id}:{self.color}:D{self.depth}"

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        return isinstance(other, FacetAddress) and self.key == other.key


class FacetCrystal:
    """En enkelt facetteret krystal med 57 facetter og dybdelag.

    Data gemmes som (eksponent, rest, base) pr. facet/farve/dybde-kombination.
    Lyskilden flyttes — krystallen sidder fast.
    """

    MAX_DEPTH = 1000
    MAX_EXPONENT = 10_000
    MAX_REST = 10**200

    def __init__(self, crystal_id: int = 0, max_depth: int = 10) -> None:
        self.crystal_id = crystal_id
        self.max_depth = min(max_depth, self.MAX_DEPTH)
        self.facets = BRILLANT_FACETS
        self.light = LightSource()

        # Sparse lagring: addr_key -> (exponent, rest, base)
        self._data: Dict[str, Tuple[int, int, int]] = {}

    @property
    def capacity(self) -> int:
        """Antal unikke adresser i denne krystal."""
        return 57 * len(COLORS) * self.max_depth

    def _validate_write(self, exp: int, rest: int, base: int) -> None:
        if exp < 0 or rest < 0 or base < 2:
            raise ValueError(f"Ugyldige værdier: exp={exp}, rest={rest}, base={base}")
        if exp > self.MAX_EXPONENT:
            raise OverflowError(f"Eksponent for stor: {exp}")
        if rest > self.MAX_REST:
            raise OverflowError(f"Rest for stor: {rest}")

    def write(
        self,
        facet_id: int,
        color: str,
        exponent: int,
        rest: int = 0,
        base: int = 2,
        depth: int = 0,
    ) -> FacetAddress:
        """Skriv data til en specifik facet/farve/dybde.

        Returnerer adressen der blev skrevet til.
        """
        addr = FacetAddress(self.crystal_id, facet_id, color, depth)
        self._validate_write(exponent, rest, base)

        # Ret lyskilden mod facetten
        self.light.aim_at_facet(FACET_BY_ID[facet_id])
        self.light.wavelength = color

        self._data[addr.key] = (exponent, rest, base)
        return addr

    def read(
        self, facet_id: int, color: str, depth: int = 0
    ) -> Tuple[int, int, int]:
        """Læs data fra facet/farve/dybde. Returnerer (exp, rest, base)."""
        addr = FacetAddress(self.crystal_id, facet_id, color, depth)
        return self._data.get(addr.key, (0, 0, 2))

    def read_value(self, facet_id: int, color: str, depth: int = 0) -> int:
        """Læs og rekonstruér den fulde talværdi."""
        exp, rest, base = self.read(facet_id, color, depth)
        return base**exp + rest

    def is_written(self, facet_id: int, color: str, depth: int = 0) -> bool:
        """Tjek om en position allerede indeholder data."""
        addr = FacetAddress(self.crystal_id, facet_id, color, depth)
        return addr.key in self._data

    def used_addresses(self) -> List[str]:
        """Returnér alle brugte adresser."""
        return list(self._data.keys())


# ---------------------------------------------------------------------------
# Multi-krystal array — kombinatorisk adresserum
# ---------------------------------------------------------------------------

class MultiCrystalArray:
    """Array af facetterede krystaller med kombinatorisk adressering.

    Med N krystaller, K farver, F facetter og D dybder:
      Total adresser = (F × K × D)^N

    Eksempel med 2 krystaller, 5 farver, 57 facetter, 10 dybder:
      (57 × 5 × 10)² = 2850² = 8.122.500 unikke adresser
    """

    def __init__(self, num_crystals: int = 1, max_depth: int = 10) -> None:
        if num_crystals < 1 or num_crystals > 100:
            raise ValueError("Antal krystaller skal være 1-100")
        self.crystals = [
            FacetCrystal(crystal_id=i, max_depth=max_depth)
            for i in range(num_crystals)
        ]

    @property
    def num_crystals(self) -> int:
        return len(self.crystals)

    @property
    def total_capacity(self) -> int:
        """Samlet adresserum for alle krystaller (simpel sum, ikke kombinatorisk)."""
        return sum(c.capacity for c in self.crystals)

    @property
    def combinatorial_capacity(self) -> int:
        """Kombinatorisk kapacitet hvis krystaller bruges i serie."""
        single = self.crystals[0].capacity if self.crystals else 0
        return single ** len(self.crystals)

    def crystal(self, crystal_id: int) -> FacetCrystal:
        if crystal_id < 0 or crystal_id >= len(self.crystals):
            raise IndexError(f"Krystal-ID {crystal_id} udenfor rækkevidde (0-{len(self.crystals)-1})")
        return self.crystals[crystal_id]

    def write(
        self,
        crystal_id: int,
        facet_id: int,
        color: str,
        exponent: int,
        rest: int = 0,
        base: int = 2,
        depth: int = 0,
    ) -> FacetAddress:
        """Skriv til en specifik krystal."""
        return self.crystal(crystal_id).write(
            facet_id, color, exponent, rest, base, depth
        )

    def read(
        self, crystal_id: int, facet_id: int, color: str, depth: int = 0
    ) -> Tuple[int, int, int]:
        """Læs fra en specifik krystal."""
        return self.crystal(crystal_id).read(facet_id, color, depth)

    def summary(self) -> Dict:
        """Overblik over array-status."""
        return {
            "antal_krystaller": self.num_crystals,
            "kapacitet_pr_krystal": self.crystals[0].capacity if self.crystals else 0,
            "total_kapacitet": self.total_capacity,
            "kombinatorisk_kapacitet": self.combinatorial_capacity,
            "brugte_adresser": sum(
                len(c.used_addresses()) for c in self.crystals
            ),
        }
