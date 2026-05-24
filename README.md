# Factory Placement MVP (Streamlit + FastAPI)

Прототип веб‑приложения для **подбора локации размещения завода** (производство сэндвич‑панелей) по ТЗ хакатона май 2026.

## Что внутри
- `apps/web` — Streamlit UI (форма инвестора + карта)
- `services/api` — FastAPI backend (ранжирование регионов, расчеты, отчеты)
- `packages/core` — расчетное ядро (площади, смета, ранжирование)
- `data/regions` — локальная JSON база регионов и площадок

## Быстрый старт (локально)

### 1) Backend
```bash
cd services/api
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2) Frontend
```bash
cd apps/web
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Конфигурация
- `OPENAI_API_KEY` — опционально (для генеративных блоков, пока заглушки).

## Статус
Это **каркас**: основные интерфейсы, структуры данных и заглушки функций добавлены для быстрого старта разработки.
