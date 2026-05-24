from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

HousingType = Literal["none", "dorm", "apartments"]
ArchitecturePriority = Literal["authentic", "techno", "eco"]
InsulationType = Literal["ppu", "minvata", "pps"]

LandscapingItem = Literal[
    "alley",
    "fountain_square",
    "gazebos",
    "stage",
    "health_trail",
    "pond",
    "art_object",
]

SportItem = Literal["street_gym", "stadium", "pool", "gym", "hockey"]


@dataclass(frozen=True)
class InvestorInput:
    # Production (4 поля в ТЗ, но UI может скрывать утеплитель при необходимости)
    volume_k_sqm_per_year: float  # 100–1000
    employees: int  # 10–200
    budget_m_rub: float  # 10–300 (по ТЗ)
    insulation_type: InsulationType

    # Logistics
    needs_railway: bool
    max_distance_to_highway_km: float

    # Architecture & style
    architecture_priority: ArchitecturePriority
    landscaping: tuple[LandscapingItem, ...]  # до 3

    # Social
    housing_share_pct: int  # 0/30/50/70
    housing_type: HousingType
    kindergarten_places_per_100: int  # 0/15/30/50
    sports: tuple[SportItem, ...]  # до 2


@dataclass(frozen=True)
class RankResult:
    region_code: str
    region_name: str
    score: float
    reasons: list[str]
