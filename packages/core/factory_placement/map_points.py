from __future__ import annotations

from typing import Any

from .data import load_regions_db


def _parse_site_from_reasons(reasons: list[str]) -> dict[str, Any] | None:
    """Достаём site_id из reasons (формат 'Площадка: NAME (ID)')."""
    for r in reasons:
        if r.startswith("Площадка:") and "(" in r and r.endswith(")"):
            try:
                site_id = r.split("(")[-1].rstrip(")").strip()
                return {"site_id": site_id}
            except Exception:
                return None
    return None


def build_map_points_from_ranking(ranking: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Возвращает точки (lat/lon) для отображения ТОП-3 на карте.

    Берём координаты из data/regions/regions_db.json по site_id, который
    записан в reasons у ranking (см. ranking.py).

    Это простой «склейщик» для фронта, чтобы сразу ставить маркеры.
    """

    db = load_regions_db()
    region_by_code = {str(r.get("code")): r for r in db.get("regions", [])}

    points: list[dict[str, Any]] = []

    for item in ranking:
        region_code = str(item.get("region_code"))
        region = region_by_code.get(region_code)
        if not region:
            continue

        region_name = str(region.get("name"))

        site_id = None
        parsed = _parse_site_from_reasons(item.get("reasons") or [])
        if parsed:
            site_id = parsed.get("site_id")

        site = None
        if site_id:
            for s in region.get("sites", []) or []:
                if str(s.get("id")) == str(site_id):
                    site = s
                    break

        # fallback: берем первую площадку если не нашли
        if site is None:
            sites = region.get("sites", []) or []
            if sites:
                site = sites[0]

        if site is None:
            # fallback на центр региона
            center = region.get("center") or {}
            lat = float(center.get("lat"))
            lon = float(center.get("lon"))
            pid = f"{region_code}-center"
            pname = f"{region_name} (центр)"
        else:
            loc = site.get("location") or {}
            lat = float(loc.get("lat"))
            lon = float(loc.get("lon"))
            pid = str(site.get("id"))
            pname = str(site.get("name"))

        points.append(
            {
                "id": pid,
                "name": pname,
                "lat": lat,
                "lon": lon,
                "region_code": region_code,
                "region_name": region_name,
                "site_id": site_id,
                "score": float(item.get("score")) if item.get("score") is not None else None,
            }
        )

    return points
