from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AreasBreakdown:
    workshop_sqm: float
    warehouse_sqm: float
    abk_sqm: float
    parking_sqm: float
    roads_sqm: float
    canteen_sqm: float
    medical_sqm: float
    kindergarten_sqm: float
    housing_sqm: float
    plot_area_sqm: float


# Нормативы из ТЗ (фиксированы для типа производства)
WORKSHOP_PER_K_SQM = 0.4  # м² / тыс. м² панелей в год
WAREHOUSE_K = 0.35
ABK_K = 0.02
PARKING_SQM_PER_CAR = 25.0
PARKING_CARS_SHARE = 0.5
MEDICAL_MIN_SQM = 20.0


def calc_areas(
    *,
    volume_k_sqm_per_year: float,
    employees: int,
    kindergarten_places: int,
    housing_share_pct: int,
    housing_sqm_per_person: float,
    roads_share: float = 0.12,
    canteen_share: float = 0.03,
    kindergarten_sqm_per_place: float = 3.0,
) -> AreasBreakdown:
    """Расчет площадей (каркас).

    Формулы основаны на ТЗ: цех, склад, АБК, парковка и т.п.
    Часть допущений (roads_share и др.) оформлены параметрами.
    """

    workshop = volume_k_sqm_per_year * WORKSHOP_PER_K_SQM
    warehouse = workshop * WAREHOUSE_K
    abk = workshop * ABK_K

    cars = employees * PARKING_CARS_SHARE
    parking = cars * PARKING_SQM_PER_CAR

    roads = (workshop + warehouse + abk + parking) * roads_share
    canteen = workshop * canteen_share

    medical = max(MEDICAL_MIN_SQM, employees * 0.2)  # допущение

    kindergarten = kindergarten_places * kindergarten_sqm_per_place

    housing_people = employees * (housing_share_pct / 100.0)
    housing = housing_people * housing_sqm_per_person

    plot_area = workshop + warehouse + abk + parking + roads + canteen + medical + kindergarten + housing

    return AreasBreakdown(
        workshop_sqm=workshop,
        warehouse_sqm=warehouse,
        abk_sqm=abk,
        parking_sqm=parking,
        roads_sqm=roads,
        canteen_sqm=canteen,
        medical_sqm=medical,
        kindergarten_sqm=kindergarten,
        housing_sqm=housing,
        plot_area_sqm=plot_area,
    )
