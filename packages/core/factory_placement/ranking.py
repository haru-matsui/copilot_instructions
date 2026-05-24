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


def _pick_best_site(region: dict[str, Any], investor: InvestorInput) -> dict[str, Any] | None:
    """Выбираем лучшую площадку региона с учётом требований инвестора.

    В ТЗ требование инвестора по логистике — ж/д и расстояние до трассы.
    Здесь делаем жёсткий фильтр по трассе (если превышено — сильно штрафуем)
    и по ж/д (если требуется — штрафуем отсутствие).

    Дополнительно учитываем site-level параметры сетей (если заданы).
    """

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

        # Local score: требования инвестора (жёстче) + логистика
        local = 0.0
        local += 2.0 if railway_ok else -2.0
        local += 2.0 if highway_ok else -3.0
        local += -0.001 * (steel.km + ins.km)

        if local > best_local:
            best_local = local
            best = {
                "site_id": str(site.get("id")),
                "site_name": str(site.get("name")),
                "steel_km": float(steel.km),
                "steel_supplier": steel.supplier_name,
                "ins_km": float(ins.km),
                "ins_supplier": ins.supplier_name,
                "railway": bool(site.get("railway")),
                "highway_km": highway_km,
                # site-level networks overrides
                "distance_to_substation_km": float(site.get("distance_to_substation_km", 0) or 0),
                "tp_fee_rub_per_kw": float(site.get("tp_fee_rub_per_kw", 0) or 0),
                "gas_available": bool(site.get("gas_available", False)),
            }

    return best


def rank_regions(investor: InvestorInput) -> list[RankResult]:
    """Ранжирование ТОП‑3 по TZ_hakaton.txt.

    Учитываем всё из ТЗ (раздел 4):
    - 4.1 Логистика: расстояние до стали, до утеплителя, радиус сбыта 300–500 км
    - 4.2 Социалка/кадры: индекс среды, сады, колледжи, аренда
    - 4.3 Экономика: льготы +20%, страх. взносы +15%, энерготариф, зарплата, экокласс
    - 4.4 Сети: газ, мощность (кВА), расстояние до подстанции, плата за ТП

    В ТЗ явно заданы ТОЛЬКО 2 численных бонуса (+20% и +15%).
    Остальное — «учитывать», поэтому базовый скоринг — взвешенная нормализация,
    после чего строго применяются бонусы.
    """

    db = load_regions_db()

    rows: list[dict[str, Any]] = []

    for region in db.get("regions", []):
        best_site = _pick_best_site(region, investor)
        if best_site is None:
            continue

        benefits = region.get("benefits") or {}
        networks = region.get("networks") or {}
        economy = region.get("economy") or {}
        social = region.get("social") or {}
        market = region.get("market") or {}

        # Уточняем сети на уровне площадки, если они заданы
        gas = bool(best_site.get("gas_available")) if "gas_available" in best_site else bool(networks.get("gas"))
        tp_fee = float(best_site.get("tp_fee_rub_per_kw") or networks.get("tp_fee_rub_per_kw") or 0)
        sub_dist = float(best_site.get("distance_to_substation_km") or networks.get("distance_to_substation_km") or 0)

        rows.append(
            {
                "region_code": str(region.get("code")),
                "region_name": str(region.get("name")),
                "site": best_site,
                "benefits": benefits,
                "networks": {**networks, "gas": gas, "tp_fee_rub_per_kw": tp_fee, "distance_to_substation_km": sub_dist},
                "economy": economy,
                "social": social,
                "market": market,
            }
        )

    if not rows:
        return []

    # ranges
    steel_vals = [r["site"]["steel_km"] for r in rows]
    ins_vals = [r["site"]["ins_km"] for r in rows]
    steel_min, steel_max = min(steel_vals), max(steel_vals)
    ins_min, ins_max = min(ins_vals), max(ins_vals)

    sales_vals = [float(r["market"].get("sales_radius_km", 0) or 0) for r in rows]
    sales_min, sales_max = min(sales_vals), max(sales_vals)

    rent_vals = [float(r["economy"].get("avg_rent_rub", 0) or 0) for r in rows]
    rent_min, rent_max = min(rent_vals), max(rent_vals)

    salary_vals = [float(r["economy"].get("avg_salary_rub_2025", 0) or 0) for r in rows]
    salary_min, salary_max = min(salary_vals), max(salary_vals)

    env_vals = [float(r["economy"].get("env_index_2024", 0) or 0) for r in rows]
    env_min, env_max = min(env_vals), max(env_vals)

    energy_vals = [float(r["economy"].get("energy_tariff_rub_kwh", 0) or 0) for r in rows]
    energy_min, energy_max = min(energy_vals), max(energy_vals)

    eco_vals = [float(r["economy"].get("eco_class_iza", 0) or 0) for r in rows]
    eco_min, eco_max = min(eco_vals), max(eco_vals)

    power_vals = [float(r["networks"].get("free_power_kva", 0) or 0) for r in rows]
    power_min, power_max = min(power_vals), max(power_vals)

    tp_fee_vals = [float(r["networks"].get("tp_fee_rub_per_kw", 0) or 0) for r in rows]
    tp_fee_min, tp_fee_max = min(tp_fee_vals), max(tp_fee_vals)

    sub_dist_vals = [float(r["networks"].get("distance_to_substation_km", 0) or 0) for r in rows]
    sub_dist_min, sub_dist_max = min(sub_dist_vals), max(sub_dist_vals)

    kinder_prov_vals = [
        float(r["social"].get("kindergarten_provision_places_per_100_children", 0) or 0) for r in rows
    ]
    kinder_prov_min, kinder_prov_max = min(kinder_prov_vals), max(kinder_prov_vals)

    results: list[RankResult] = []

    # weights
    W_LOGISTICS = 0.28
    W_NETWORKS = 0.22
    W_ECONOMY = 0.18
    W_SOCIAL = 0.18
    W_ACCESS = 0.14

    for r in rows:
        site = r["site"]
        reasons: list[str] = []

        # logistics
        steel_score = _score_inverse(site["steel_km"], steel_min, steel_max)
        ins_score = _score_inverse(site["ins_km"], ins_min, ins_max)

        sales_radius = float(r["market"].get("sales_radius_km", 0) or 0)
        # лучше, когда ближе к 300 (в рамках 300–500). Если данные вне диапазона — clamp.
        sales_score = 1.0 - max(0.0, min(1.0, (sales_radius - 300.0) / 200.0))

        logistics = 0.55 * steel_score + 0.30 * ins_score + 0.15 * sales_score

        # networks
        gas = bool(r["networks"].get("gas"))
        gas_score = 1.0 if gas else 0.0

        power_kva = float(r["networks"].get("free_power_kva", 0) or 0)
        power_score = _norm_minmax(power_kva, power_min, power_max)

        tp_fee = float(r["networks"].get("tp_fee_rub_per_kw", 0) or 0)
        tp_fee_score = _score_inverse(tp_fee, tp_fee_min, tp_fee_max)

        sub_dist = float(r["networks"].get("distance_to_substation_km", 0) or 0)
        sub_dist_score = _score_inverse(sub_dist, sub_dist_min, sub_dist_max)

        networks_score = 0.40 * gas_score + 0.30 * power_score + 0.15 * tp_fee_score + 0.15 * sub_dist_score

        # economy
        energy = float(r["economy"].get("energy_tariff_rub_kwh", 0) or 0)
        energy_score = _score_inverse(energy, energy_min, energy_max)

        salary = float(r["economy"].get("avg_salary_rub_2025", 0) or 0)
        salary_score = _score_inverse(salary, salary_min, salary_max)

        eco_class = float(r["economy"].get("eco_class_iza", 0) or 0)
        eco_score = _score_inverse(eco_class, eco_min, eco_max)  # ниже класс => лучше

        economy_score = 0.45 * energy_score + 0.35 * salary_score + 0.20 * eco_score

        # social
        env = float(r["economy"].get("env_index_2024", 0) or 0)
        env_score = _norm_minmax(env, env_min, env_max)

        rent = float(r["economy"].get("avg_rent_rub", 0) or 0)
        rent_score = _score_inverse(rent, rent_min, rent_max)

        kinder_prov = float(r["social"].get("kindergarten_provision_places_per_100_children", 0) or 0)
        kinder_prov_score = _norm_minmax(kinder_prov, kinder_prov_min, kinder_prov_max)

        colleges = r["social"].get("colleges") or []
        colleges_score = 1.0 if len(colleges) > 0 else 0.0

        social_score = 0.40 * env_score + 0.25 * rent_score + 0.20 * kinder_prov_score + 0.15 * colleges_score

        # access
        railway_ok = (not investor.needs_railway) or bool(site["railway"])
        highway_ok = float(site["highway_km"]) <= investor.max_distance_to_highway_km
        access = (1.0 if railway_ok else 0.0) * 0.6 + (1.0 if highway_ok else 0.0) * 0.4

        base_score = (
            W_LOGISTICS * logistics
            + W_NETWORKS * networks_score
            + W_ECONOMY * economy_score
            + W_SOCIAL * social_score
            + W_ACCESS * access
        )

        # tz bonuses (strict)
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

        # reasons
        reasons.append(f"Площадка: {site['site_name']} ({site['site_id']})")
        reasons.append(f"Сбыт (радиус): {sales_radius:.0f} км")
        reasons.append(f"Сталь: {site['steel_km']:.0f} км ({site['steel_supplier']})")
        reasons.append(f"Утеплитель: {site['ins_km']:.0f} км ({site['ins_supplier']})")
        reasons.append(f"Энерготариф: {energy:.2f} руб/кВт·ч")
        reasons.append(f"Зарплата: {salary:.0f} руб/мес")
        reasons.append(
            f"Сети: газ={'есть' if gas else 'нет'}, мощность={power_kva:.0f} кВА, TP={tp_fee:.0f} руб/кВт, подстанция={sub_dist:.1f} км"
        )
        reasons.append(
            f"Соц.: индекс среды={env:.0f}, аренда={rent:.0f}, сады={kinder_prov:.0f}, колледжи={len(colleges)}"
        )
        if investor.needs_railway:
            reasons.append(f"Ж/д ветка: {'да' if site['railway'] else 'нет'}")
        reasons.append(f"До трассы: {site['highway_km']:.0f} км")

        results.append(RankResult(r["region_code"], r["region_name"], float(final), reasons))

    results.sort(key=lambda x: x.score, reverse=True)
    return results[:3]
