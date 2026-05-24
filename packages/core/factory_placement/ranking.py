from __future__ import annotations

from typing import Any

from .data import load_regions_db
from .geo import LatLon
from .logistics import min_distance_km
from .models import InvestorInput, RankResult
from .suppliers import SUPPLIERS_INSULATION, SUPPLIERS_STEEL


def _norm_minmax(value: float, min_v: float, max_v: float) -> float:
    if max_v <= min_v:
        return 0.0
    v = (value - min_v) / (max_v - min_v)
    return max(0.0, min(1.0, v))


def _score_inverse(value: float, min_v: float, max_v: float) -> float:
    """Нормализация, где меньше = лучше (1..0)."""
    return 1.0 - _norm_minmax(value, min_v, max_v)


def rank_regions(investor: InvestorInput) -> list[RankResult]:
    """Ранжирование ТОП‑3 по TZ_hakaton.txt.

    Что учитываем (раздел 4):
    - 4.1 Логистика: расстояние до стали, расстояние до утеплителя, радиус сбыта 300–500 км
    - 4.2 Социалка/кадры: индекс среды, обеспеченность садами, колледжи, аренда
    - 4.3 Экономика: льготы +20%, страх. взносы +15%, энерготариф, средняя зарплата
    - 4.4 Сети: газ, свободная мощность, расстояние до подстанции, плата за техприсоединение

    В ТЗ явно заданы ТОЛЬКО 2 весовых бонуса:
    - налоговые льготы (ТОР/ОЭЗ/промпарк): +20%
    - снижение страховых взносов (7,6% вместо 30%): +15%

    Для остальных факторов ТЗ перечисляет «что учитывать», но не фиксирует веса.
    Поэтому:
    - базовый скоринг — нормализованная сумма по группам факторов;
    - затем строго применяем бонусы *1.20 и *1.15.
    """

    db = load_regions_db()

    # Метрики на уровне лучшей площадки региона
    rows: list[dict[str, Any]] = []

    for region in db.get("regions", []):
        benefits = region.get("benefits") or {}
        networks = region.get("networks") or {}
        economy = region.get("economy") or {}
        social = region.get("social") or {}

        best: dict[str, Any] | None = None
        best_local = -1e18

        for site in region.get("sites", []):
            loc = site.get("location") or {}
            origin = LatLon(lat=float(loc.get("lat")), lon=float(loc.get("lon")))

            steel = min_distance_km(origin=origin, suppliers=SUPPLIERS_STEEL)
            ins = min_distance_km(origin=origin, suppliers=SUPPLIERS_INSULATION)

            railway_ok = (not investor.needs_railway) or bool(site.get("railway"))
            highway_km = float(site.get("distance_to_highway_km", 9999))
            highway_ok = highway_km <= investor.max_distance_to_highway_km

            # Локальный отбор площадки: соответствие требованиям + логистика
            local = 0.0
            local += 1.0 if railway_ok else -1.0
            local += 1.0 if highway_ok else -1.0
            local += -0.001 * (steel.km + ins.km)

            if local > best_local:
                best_local = local
                best = {
                    "region_code": str(region.get("code")),
                    "region_name": str(region.get("name")),
                    "steel_km": float(steel.km),
                    "steel_supplier": steel.supplier_name,
                    "ins_km": float(ins.km),
                    "ins_supplier": ins.supplier_name,
                    "railway": bool(site.get("railway")),
                    "highway_km": highway_km,
                    "benefits": benefits,
                    "networks": networks,
                    "economy": economy,
                    "social": social,
                    "site_id": str(site.get("id")),
                    "site_name": str(site.get("name")),
                }

        if best is not None:
            rows.append(best)

    if not rows:
        return []

    # Диапазоны для нормализации
    steel_min, steel_max = min(r["steel_km"] for r in rows), max(r["steel_km"] for r in rows)
    ins_min, ins_max = min(r["ins_km"] for r in rows), max(r["ins_km"] for r in rows)

    rent_vals = [float(r["economy"].get("avg_rent_rub", 0) or 0) for r in rows]
    rent_min, rent_max = min(rent_vals), max(rent_vals)

    salary_vals = [float(r["economy"].get("avg_salary_rub_2025", 0) or 0) for r in rows]
    salary_min, salary_max = min(salary_vals), max(salary_vals)

    env_vals = [float(r["economy"].get("env_index_2024", 0) or 0) for r in rows]
    env_min, env_max = min(env_vals), max(env_vals)

    energy_vals = [float(r["economy"].get("energy_tariff_rub_kwh", 0) or 0) for r in rows]
    energy_min, energy_max = min(energy_vals), max(energy_vals)

    tp_fee_vals = [float(r["networks"].get("tp_fee_rub_per_kw", 0) or 0) for r in rows]
    tp_fee_min, tp_fee_max = min(tp_fee_vals), max(tp_fee_vals)

    sub_dist_vals = [float(r["networks"].get("distance_to_substation_km", 0) or 0) for r in rows]
    sub_dist_min, sub_dist_max = min(sub_dist_vals), max(sub_dist_vals)

    power_vals = [float(r["networks"].get("free_power_mw", 0) or 0) for r in rows]
    power_min, power_max = min(power_vals), max(power_vals)

    kinder_prov_vals = [
        float(r["social"].get("kindergarten_provision_places_per_100_children", 0) or 0) for r in rows
    ]
    kinder_prov_min, kinder_prov_max = min(kinder_prov_vals), max(kinder_prov_vals)

    results: list[RankResult] = []

    # Базовые веса групп (ТЗ их не фиксирует; можно скорректировать, но сумма = 1.0)
    W_LOGISTICS = 0.28
    W_NETWORKS = 0.22
    W_ECONOMY = 0.18
    W_SOCIAL = 0.18
    W_ACCESS = 0.14

    for r in rows:
        reasons: list[str] = []

        # 4.1 Логистика
        steel_score = _score_inverse(r["steel_km"], steel_min, steel_max)
        ins_score = _score_inverse(r["ins_km"], ins_min, ins_max)

        # Радиус сбыта (300–500 км): в MVP считаем, что чем ближе к 300 км, тем лучше.
        # При отсутствии отдельного показателя рынка используем прокси: среднее расстояние до сырья.
        sales_radius_proxy = (r["steel_km"] + r["ins_km"]) / 2.0
        # Нормируем по 300..500: 1 на 300, 0 на 500
        sales_score = max(0.0, min(1.0, (500.0 - sales_radius_proxy) / 200.0))

        logistics = 0.55 * steel_score + 0.30 * ins_score + 0.15 * sales_score

        # 4.4 Сети
        gas = bool(r["networks"].get("gas"))
        gas_score = 1.0 if gas else 0.0

        power = float(r["networks"].get("free_power_mw", 0) or 0)
        power_score = _norm_minmax(power, power_min, power_max)

        tp_fee = float(r["networks"].get("tp_fee_rub_per_kw", 0) or 0)
        tp_fee_score = _score_inverse(tp_fee, tp_fee_min, tp_fee_max)

        sub_dist = float(r["networks"].get("distance_to_substation_km", 0) or 0)
        sub_dist_score = _score_inverse(sub_dist, sub_dist_min, sub_dist_max)

        networks = 0.40 * gas_score + 0.30 * power_score + 0.15 * tp_fee_score + 0.15 * sub_dist_score

        # 4.3 Экономика
        energy = float(r["economy"].get("energy_tariff_rub_kwh", 0) or 0)
        energy_score = _score_inverse(energy, energy_min, energy_max)

        salary = float(r["economy"].get("avg_salary_rub_2025", 0) or 0)
        salary_score = _score_inverse(salary, salary_min, salary_max)  # меньше ЗП => ниже ФОТ

        economy = 0.55 * energy_score + 0.45 * salary_score

        # 4.2 Социалка/кадры
        env = float(r["economy"].get("env_index_2024", 0) or 0)
        env_score = _norm_minmax(env, env_min, env_max)

        rent = float(r["economy"].get("avg_rent_rub", 0) or 0)
        rent_score = _score_inverse(rent, rent_min, rent_max)

        kinder_prov = float(r["social"].get("kindergarten_provision_places_per_100_children", 0) or 0)
        kinder_prov_score = _norm_minmax(kinder_prov, kinder_prov_min, kinder_prov_max)

        colleges = r["social"].get("colleges") or []
        colleges_score = 1.0 if len(colleges) > 0 else 0.0

        social_score = 0.40 * env_score + 0.25 * rent_score + 0.20 * kinder_prov_score + 0.15 * colleges_score

        # Доступность под требования инвестора
        railway_ok = (not investor.needs_railway) or bool(r["railway"])
        highway_ok = float(r["highway_km"]) <= investor.max_distance_to_highway_km
        access = (1.0 if railway_ok else 0.0) * 0.6 + (1.0 if highway_ok else 0.0) * 0.4

        base_score = (
            W_LOGISTICS * logistics
            + W_NETWORKS * networks
            + W_ECONOMY * economy
            + W_SOCIAL * social_score
            + W_ACCESS * access
        )

        # Бонусы из ТЗ (строго)
        benefits = r["benefits"]
        has_tax_benefits = bool(benefits.get("oez") or benefits.get("tor") or benefits.get("industrial_park"))
        has_social_contrib_benefit = bool(benefits.get("reduced_insurance"))

        final = base_score
        if has_tax_benefits:
            final *= 1.20
            reasons.append("Налоговые льготы (ТОР/ОЭЗ/промпарк): +20%")
        if has_social_contrib_benefit:
            final *= 1.15
            reasons.append("Снижение страховых взносов (7,6% вместо 30%): +15%")

        # Причины
        reasons.append(f"Площадка: {r['site_name']} ({r['site_id']})")
        reasons.append(f"Сталь: {r['steel_km']:.0f} км ({r['steel_supplier']})")
        reasons.append(f"Утеплитель: {r['ins_km']:.0f} км ({r['ins_supplier']})")
        reasons.append(f"Энерготариф: {energy:.2f} руб/кВт·ч")
        reasons.append(f"Зарплата: {salary:.0f} руб/мес")
        reasons.append(
            f"Сети: газ={'есть' if gas else 'нет'}, мощность={power:.0f} МВт, TP={tp_fee:.0f} руб/кВт, подстанция={sub_dist:.1f} км"
        )
        reasons.append(
            f"Соц.: индекс среды={env:.0f}, аренда={rent:.0f}, сады={kinder_prov:.0f}, колледжи={len(colleges)}"
        )
        if investor.needs_railway:
            reasons.append(f"Ж/д ветка: {'да' if r['railway'] else 'нет'}")
        reasons.append(f"До трассы: {r['highway_km']:.0f} км")

        results.append(RankResult(r["region_code"], r["region_name"], float(final), reasons))

    results.sort(key=lambda x: x.score, reverse=True)
    return results[:3]
