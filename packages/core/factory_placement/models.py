from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

HousingType = Literal["none", "dorm", "apartments"]
ArchitecturePriority = Literal["authentic", "techno", "eco"]


@dataclass(frozen=True)
class InvestorInput:
    # Production
    volume_k_sqm_per_year: float  # тыс. м²/год
    employees: int
    budget_m_rub: float

    # Logistics
    needs_railway: bool
    max_distance_to_highway_km: float

    # Architecture & social
    architecture_priority: ArchitecturePriority
    landscaping_level: int  # 0..100 (условно)
    housing_share_pct: int  # 0/30/50/70
    housing_type: HousingType
    kindergarten_places_per_100: int


@dataclass(frozen=True)
class RegionCandidate:
    region_code: str
    region_name: str


@dataclass(frozen=True)
class RankResult:
    region_code: str
    region_name: str
    score: float
    reasons: list[str]
