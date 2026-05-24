from __future__ import annotations

from dataclasses import asdict

from .areas import calc_areas
from .costs import calc_costs
from .models import InvestorInput, RankResult
from .ranking import rank_regions


def evaluate(investor: InvestorInput) -> dict:
    """Единая точка входа: расчёты + ранжирование."""

    areas = calc_areas(
        volume_k_sqm_per_year=investor.volume_k_sqm_per_year,
        employees=investor.employees,
        housing_share_pct=investor.housing_share_pct,
        housing_type=investor.housing_type,
        kindergarten_places_per_100_employees=investor.kindergarten_places_per_100,
    )

    costs = calc_costs(areas=areas, housing_type=investor.housing_type, sports=list(investor.sports))

    ranking: list[RankResult] = rank_regions(investor)

    return {
        "investor": asdict(investor),
        "areas": asdict(areas),
        "costs": asdict(costs),
        "ranking": [asdict(r) for r in ranking],
    }
