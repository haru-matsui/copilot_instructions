from __future__ import annotations

from fastapi import APIRouter

from ..schemas import EvaluationResponseSchema, InvestorInputSchema

from packages.core.factory_placement.models import InvestorInput
from packages.core.factory_placement.service import evaluate

router = APIRouter(prefix="/v1", tags=["factory-placement"])


@router.post("/evaluate", response_model=EvaluationResponseSchema)
def post_evaluate(payload: InvestorInputSchema):
    investor = InvestorInput(**payload.model_dump())
    result = evaluate(investor)

    return {
        "areas": result["areas"],
        "costs": result["costs"],
        "ranking": result["ranking"],
        "debug": {"investor": result["investor"]},
    }
