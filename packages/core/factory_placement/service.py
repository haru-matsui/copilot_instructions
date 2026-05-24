from __future__ import annotations

from dataclasses import asdict

from .costs import calc_costs
from .areas import calc_areas
from .models import InvestorInput, RankResult
from .ranking import rank_regions


def evaluate(investor: InvestorInput) -> dict:
    """Единая точка входа для backend: расчет + ранжирование."""

    # допущение по жилью
    housing_sqm_per_person = 6.0 if investor.housing_type == "dorm" else 18.0

    kindergarten_places = int(investor.employees * investor.kindergarten_places_per_100 / 100)

    areas = calc_areas(
        volume_k_sqm_per_year=investor.volume_k_sqm_per_year,
        employees=investor.employees,
        kindergarten_places=kindergarten_places,
        housing_share_pct=investor.housing_share_pct,
        housing_sqm_per_person=housing_sqm_per_person,
    )

    costs = calc_costs(areas=areas, housing_type=investor.housing_type)

    ranking: list[RankResult] = rank_regions(investor)

    return {
        "investor": asdict(investor),
        "areas": asdict(areas),
        "costs": asdict(costs),
        "ranking": [asdict(r) for r in ranking],
    }
