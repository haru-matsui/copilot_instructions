from __future__ import annotations

import requests


def generate_report_md(*, gemini_api_key: str, context: dict) -> str:
    """Генерация markdown отчета через Gemini API.

    Используем Generative Language API (v1beta) и модель gemini-1.5-flash.
    """

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

    prompt = (
        "Сгенерируй аналитическую справку (Markdown) по размещению завода сэндвич-панелей.\n"
        "Структура строго по ТЗ:\n"
        "1) Социальный паспорт региона (индекс среды, сады, колледжи, аренда)\n"
        "2) Экономический блок (льготы, энерготариф, средняя зарплата)\n"
        "3) Сетевой блок (газ, свободная мощность, стоимость подключения)\n"
        "4) Логистика сырья (расстояния до стали и утеплителя)\n"
        "5) Рекомендации по удержанию персонала (жильё, транспорт; автобусы при удалённости >15 км)\n"
        "6) Предварительная смета строительства\n\n"
        "Контекст (JSON):\n"
        f"{context}"
    )

    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    resp = requests.post(url, params={"key": gemini_api_key}, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return str(data)
