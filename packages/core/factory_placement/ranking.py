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


def rank_regions(investor: InvestorInput) -> list[RankResult]:
    """Ранжирование ТОП‑3 строго по параметрам/бонусам ТЗ.

    В TZ_hakaton.txt явно заданы 2 весовых бонуса:
    - наличие налоговых льгот (ТОР/ОЭЗ/промпарк): +20%
    - снижение страховых взносов: +15%

    Остальные параметры описаны как влияющие на расчёт/ранжирование, без конкретных весов.
    Поэтому реализуем:
    1) базовую нормализованную сумму по группам факторов;
    2) затем строго применяем мультипликативные бонусы +20% и +15%.

    Если появятся точные веса остальных групп — их легко зафиксировать в константах ниже.
    """

    db = load_regions_db()

    # Считаем метрики на уровне лучшей площадки региона
    rows: list[dict[str, Any]] = []

    for region in db.get("regions", []):
        benefits = region.get("benefits") or {}
        networks = region.get("networks") or {}
        economy = region.get("economy") or {}

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

            # Локальный отбор площадки: доступность + логистика
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

    power_vals = [float(r["networks"].get("free_power_mw", 0) or 0) for r in rows]
    power_min, power_max = min(power_vals), max(power_vals)

    results: list[RankResult] = []

    # Базовые веса групп (не фиксированы в ТЗ, но требуются для численного ранжирования)
    W_LOGISTICS = 0.35
    W_NETWORKS = 0.25
    W_SOCIAL = 0.20
    W_ACCESS = 0.20

    for r in rows:
        reasons: list[str] = []

        steel_score = 1.0 - _norm_minmax(r["steel_km"], steel_min, steel_max)
        ins_score = 1.0 - _norm_minmax(r["ins_km"], ins_min, ins_max)
        logistics = 0.6 * steel_score + 0.4 * ins_score

        gas = bool(r["networks"].get("gas"))
        gas_score = 1.0 if gas else 0.0
        power = float(r["networks"].get("free_power_mw", 0) or 0)
        power_score = _norm_minmax(power, power_min, power_max)
        networks = 0.6 * gas_score + 0.4 * power_score

        env_score = _norm_minmax(float(r["economy"].get("env_index_2024", 0) or 0), env_min, env_max)
        rent_score = 1.0 - _norm_minmax(float(r["economy"].get("avg_rent_rub", 0) or 0), rent_min, rent_max)
        salary_score = 1.0 - _norm_minmax(float(r["economy"].get("avg_salary_rub_2025", 0) or 0), salary_min, salary_max)
        social = 0.45 * env_score + 0.35 * rent_score + 0.20 * salary_score

        railway_ok = (not investor.needs_railway) or bool(r["railway"])
        highway_ok = float(r["highway_km"]) <= investor.max_distance_to_highway_km
        access = (1.0 if railway_ok else 0.0) * 0.6 + (1.0 if highway_ok else 0.0) * 0.4

        base_score = W_LOGISTICS * logistics + W_NETWORKS * networks + W_SOCIAL * social + W_ACCESS * access

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

        reasons.append(f"Сталь: {r['steel_km']:.0f} км ({r['steel_supplier']})")
        reasons.append(f"Утеплитель: {r['ins_km']:.0f} км ({r['ins_supplier']})")
        reasons.append(f"Газ: {'есть' if gas else 'нет'}, мощность: {power:.0f} МВт")
        if investor.needs_railway:
            reasons.append(f"Ж/д ветка: {'да' if r['railway'] else 'нет'}")
        reasons.append(f"До трассы: {r['highway_km']:.0f} км")

        results.append(RankResult(r["region_code"], r["region_name"], float(final), reasons))

    results.sort(key=lambda x: x.score, reverse=True)
    return results[:3]
