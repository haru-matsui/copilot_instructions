from __future__ import annotations

from dataclasses import dataclass

from .areas import AreasBreakdown


@dataclass(frozen=True)
class CostBreakdown:
    buildings_cost_rub: float
    landscaping_cost_rub: float
    sports_cost_rub: float
    total_cost_rub: float


# Нормативы стоимости из ТЗ (6.3)
PRICE_WORKSHOP_WAREHOUSE = 35_000
PRICE_ABK = 55_000
PRICE_HOUSING_DORM = 70_000
PRICE_HOUSING_APT = 90_000
PRICE_KINDERGARTEN = 50_000
PRICE_CANTEEN = 35_000
PRICE_MEDICAL = 45_000
PRICE_ROADS_PARKING = 5_000
LANDSCAPING_PER_SQM = 2_000

# Спортобъекты (штучно)
SPORT_STADIUM = 5_000_000
SPORT_POOL = 8_000_000
SPORT_GYM = 3_000_000
SPORT_HOCKEY = 2_000_000


def calc_costs(
    *,
    areas: AreasBreakdown,
    housing_type: str,
    landscaping_area_sqm: float | None = None,
    sports: list[str] | None = None,
) -> CostBreakdown:
    """Укрупнённая смета строго по ТЗ (6.3)."""

    sports = sports or []

    workshop_warehouse = areas.workshop_sqm + areas.warehouse_sqm

    buildings = 0.0
    buildings += workshop_warehouse * PRICE_WORKSHOP_WAREHOUSE
    buildings += areas.abk_sqm * PRICE_ABK

    if housing_type == "dorm":
        buildings += areas.housing_sqm * PRICE_HOUSING_DORM
    elif housing_type == "apartments":
        buildings += areas.housing_sqm * PRICE_HOUSING_APT

    buildings += areas.kindergarten_sqm * PRICE_KINDERGARTEN
    buildings += areas.canteen_sqm * PRICE_CANTEEN
    buildings += areas.medical_sqm * PRICE_MEDICAL

    # дороги + парковка
    buildings += (areas.roads_sqm + areas.parking_sqm) * PRICE_ROADS_PARKING

    # благоустройство: 2000 руб/м² участка
    land_area = areas.plot_area_sqm if landscaping_area_sqm is None else landscaping_area_sqm
    landscaping = land_area * LANDSCAPING_PER_SQM

    # спорт
    sports_cost = 0.0
    for s in sports:
        if s == "stadium":
            sports_cost += SPORT_STADIUM
        elif s == "pool":
            sports_cost += SPORT_POOL
        elif s == "gym":
            sports_cost += SPORT_GYM
        elif s == "hockey":
            sports_cost += SPORT_HOCKEY

    total = buildings + landscaping + sports_cost

    return CostBreakdown(
        buildings_cost_rub=buildings,
        landscaping_cost_rub=landscaping,
        sports_cost_rub=sports_cost,
        total_cost_rub=total,
    )
