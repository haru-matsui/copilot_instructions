from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Literal, List, Optional

ArchitecturePriority = Literal["authentic", "techno", "eco"]
HousingType = Literal["none", "dorm", "apartments"]
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


class InvestorInputSchema(BaseModel):
    # Production
    volume_k_sqm_per_year: float = Field(ge=100, le=1000, description="тыс. м² панелей в год")
    employees: int = Field(ge=10, le=200)
    budget_m_rub: float = Field(ge=10, le=300, description="бюджет, млн руб")
    insulation_type: InsulationType

    # Logistics
    needs_railway: bool
    max_distance_to_highway_km: float = Field(ge=1, le=100)

    # Architecture & style
    architecture_priority: ArchitecturePriority
    landscaping: List[LandscapingItem] = Field(default_factory=list, max_length=3)

    # Social
    housing_share_pct: int = Field(ge=0, le=100)
    housing_type: HousingType
    kindergarten_places_per_100: int = Field(ge=0, le=50)
    sports: List[SportItem] = Field(default_factory=list, max_length=2)

    # LLM
    gemini_api_key: Optional[str] = Field(default=None, description="API key для Gemini")


class RankItemSchema(BaseModel):
    region_code: str
    region_name: str
    score: float
    reasons: List[str]


class EvaluationResponseSchema(BaseModel):
    areas: dict
    costs: dict
    ranking: List[RankItemSchema]
    report_md: Optional[str] = None
    debug: Optional[dict] = None
