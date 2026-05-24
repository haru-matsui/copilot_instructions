from __future__ import annotations

from dataclasses import dataclass

from .areas import AreasBreakdown


@dataclass(frozen=True)
class CostBreakdown:
    buildings_cost_rub: float
    landscaping_cost_rub: float
    total_cost_rub: float


# Нормативы стоимости из ТЗ (руб/м²)
PRICE_WORKSHOP_WAREHOUSE = 35_000
PRICE_ABK = 55_000
PRICE_HOUSING_DORM = 70_000
PRICE_HOUSING_APT = 90_000
PRICE_KINDERGARTEN = 50_000
PRICE_CANTEEN = 35_000
PRICE_MEDICAL = 45_000
PRICE_ROADS_PARKING = 20_000  # допущение


def calc_costs(*, areas: AreasBreakdown, housing_type: str, landscaping_per_sqm: float = 1500.0) -> CostBreakdown:
    """Укрупненна�� смета (каркас)."""

    workshop_warehouse = areas.workshop_sqm + areas.warehouse_sqm
    buildings = 0.0
    buildings += workshop_warehouse * PRICE_WORKSHOP_WAREHOUSE
    buildings += areas.abk_sqm * PRICE_ABK

    if housing_type == "dorm":
        buildings += areas.housing_sqm * PRICE_HOUSING_DORM
    elif housing_type == "apartments":
        buildings += areas.housing_sqm * PRICE_HOUSING_APT
    else:
        buildings += 0.0

    buildings += areas.kindergarten_sqm * PRICE_KINDERGARTEN
    buildings += areas.canteen_sqm * PRICE_CANTEEN
    buildings += areas.medical_sqm * PRICE_MEDICAL

    # дороги/парковка
    buildings += (areas.roads_sqm + areas.parking_sqm) * PRICE_ROADS_PARKING

    landscaping = areas.plot_area_sqm * landscaping_per_sqm
    total = buildings + landscaping

    return CostBreakdown(buildings_cost_rub=buildings, landscaping_cost_rub=landscaping, total_cost_rub=total)
