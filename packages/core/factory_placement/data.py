from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "regions"


def load_regions_db() -> dict[str, Any]:
    """Загружает локальную JSON базу регионов/площадок."""
    path = DATA_DIR / "regions_db.json"
    return json.loads(path.read_text(encoding="utf-8"))
