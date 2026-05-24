from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AreasBreakdown:
    workshop_sqm: float
    warehouse_sqm: float
    abk_sqm: float
    parking_sqm: float
    roads_sqm: float
    housing_sqm: float
    kindergarten_sqm: float
    canteen_sqm: float
    medical_sqm: float
    plot_area_sqm: float


# Нормативы из ТЗ (раздел 6)
WORKSHOP_PER_K_SQM = 0.4  # м² / тыс. м² панелей в год
WAREHOUSE_K = 0.35
ABK_K = 0.02

PARKING_CARS_SHARE = 0.5
PARKING_SQM_PER_CAR = 25.0

ROADS_K = 0.25  # (цех + склад) * 0.25

CANTEEN_SQM_PER_EMP = 0.5

MEDICAL_SQM_PER_EMP = 0.1
MEDICAL_MIN_SQM = 20.0

KINDERGARTEN_SQM_PER_PLACE = 15.0

# Жильё: сотрудники * %жилья * (25 / 40) (общежитие / квартиры)
HOUSING_SQM_PER_PERSON_DORM = 25.0
HOUSING_SQM_PER_PERSON_APT = 40.0


def calc_areas(
    *,
    volume_k_sqm_per_year: float,
    employees: int,
    housing_share_pct: int,
    housing_type: str,
    kindergarten_places_per_100_employees: int,
) -> AreasBreakdown:
    """Расчёт площадей строго по формулам ТЗ (6.2)."""

    workshop = volume_k_sqm_per_year * WORKSHOP_PER_K_SQM
    warehouse = workshop * WAREHOUSE_K
    abk = workshop * ABK_K

    parking = employees * PARKING_CARS_SHARE * PARKING_SQM_PER_CAR
    roads = (workshop + warehouse) * ROADS_K

    # жильё
    housing_people = employees * (housing_share_pct / 100.0)
    if housing_type == "dorm":
        housing = housing_people * HOUSING_SQM_PER_PERSON_DORM
    elif housing_type == "apartments":
        housing = housing_people * HOUSING_SQM_PER_PERSON_APT
    else:
        housing = 0.0

    # детсад
    kindergarten_places = (employees / 100.0) * float(kindergarten_places_per_100_employees)
    kindergarten = kindergarten_places * KINDERGARTEN_SQM_PER_PLACE

    # столовая
    canteen = employees * CANTEEN_SQM_PER_EMP

    # медпункт
    medical = max(MEDICAL_MIN_SQM, employees * MEDICAL_SQM_PER_EMP)

    plot_area = (
        workshop
        + warehouse
        + abk
        + parking
        + roads
        + housing
        + kindergarten
        + canteen
        + medical
    )

    return AreasBreakdown(
        workshop_sqm=workshop,
        warehouse_sqm=warehouse,
        abk_sqm=abk,
        parking_sqm=parking,
        roads_sqm=roads,
        housing_sqm=housing,
        kindergarten_sqm=kindergarten,
        canteen_sqm=canteen,
        medical_sqm=medical,
        plot_area_sqm=plot_area,
    )
