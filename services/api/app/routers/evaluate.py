from __future__ import annotations

from fastapi import APIRouter

from ..schemas import EvaluationResponseSchema, InvestorInputSchema

from packages.core.factory_placement.models import InvestorInput
from packages.core.factory_placement.service import evaluate

from ..llm.gemini import generate_report_md

router = APIRouter(prefix="/v1", tags=["factory-placement"])


def _fallback_report_md(result: dict) -> str:
    # Шаблон по разделу 7.1 ТЗ
    top = result["ranking"][0] if result.get("ranking") else None
    lines: list[str] = []
    lines.append("# Аналитическая справка")
    if top:
        lines.append(f"## Рекомендуемый регион: {top['region_name']}")

    lines.append("## Социальный паспорт региона")
    lines.append("(индекс среды, сады, колледжи, аренда) — в MVP подтягивается из JSON базы")

    lines.append("## Экономический блок")
    lines.append("(льготы, энерготариф, средняя зарплата) — в MVP частично")

    lines.append("## Сетевой блок")
    lines.append("(газ, свободная мощность, стоимость подключения) — в MVP частично")

    lines.append("## Логистика сырья")
    for r in result.get("ranking", [])[:1]:
        for reason in r.get("reasons", []):
            if reason.startswith("Сталь") or reason.startswith("Утеплитель"):
                lines.append(f"- {reason}")

    lines.append("## Рекомендации по удержанию персонала")
    lines.append("- Жильё, транспорт, корпоративные автобусы при удалённости >15 км")

    lines.append("## Предварительная смета")
    for k, v in result.get("costs", {}).items():
        lines.append(f"- **{k}**: {v}")

    lines.append("\n## Приложение: расчёт площадей")
    for k, v in result.get("areas", {}).items():
        lines.append(f"- **{k}**: {v}")

    return "\n".join(lines) + "\n"


@router.post("/evaluate", response_model=EvaluationResponseSchema)
def post_evaluate(payload: InvestorInputSchema):
    investor = InvestorInput(
        volume_k_sqm_per_year=payload.volume_k_sqm_per_year,
        employees=payload.employees,
        budget_m_rub=payload.budget_m_rub,
        insulation_type=payload.insulation_type,
        needs_railway=payload.needs_railway,
        max_distance_to_highway_km=payload.max_distance_to_highway_km,
        architecture_priority=payload.architecture_priority,
        landscaping=tuple(payload.landscaping),
        housing_share_pct=payload.housing_share_pct,
        housing_type=payload.housing_type,
        kindergarten_places_per_100=payload.kindergarten_places_per_100,
        sports=tuple(payload.sports),
    )

    result = evaluate(investor)

    report_md = None
    if payload.gemini_api_key:
        try:
            report_md = generate_report_md(gemini_api_key=payload.gemini_api_key, context=result)
        except Exception:
            report_md = _fallback_report_md(result)
    else:
        report_md = _fallback_report_md(result)

    return {
        "areas": result["areas"],
        "costs": result["costs"],
        "ranking": result["ranking"],
        "report_md": report_md,
        "debug": {"investor": result["investor"]},
    }
