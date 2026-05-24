from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Literal, List, Optional

ArchitecturePriority = Literal["authentic", "techno", "eco"]
HousingType = Literal["none", "dorm", "apartments"]


class InvestorInputSchema(BaseModel):
    # Production
    volume_k_sqm_per_year: float = Field(ge=100, le=1000, description="тыс. м² панелей в год")
    employees: int = Field(ge=10, le=200)
    budget_m_rub: float = Field(ge=50, le=5000, description="бюджет, млн руб")

    # Logistics
    needs_railway: bool
    max_distance_to_highway_km: float = Field(ge=1, le=100)

    # Architecture & social
    architecture_priority: ArchitecturePriority
    landscaping_level: int = Field(ge=0, le=100)
    housing_share_pct: int = Field(ge=0, le=100)
    housing_type: HousingType
    kindergarten_places_per_100: int = Field(ge=0, le=100)


class RankItemSchema(BaseModel):
    region_code: str
    region_name: str
    score: float
    reasons: List[str]


class EvaluationResponseSchema(BaseModel):
    areas: dict
    costs: dict
    ranking: List[RankItemSchema]
    debug: Optional[dict] = None
