from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import evaluate


def create_app() -> FastAPI:
    app = FastAPI(title="Factory Placement API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"] ,
        allow_headers=["*"] ,
    )

    app.include_router(evaluate.router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
