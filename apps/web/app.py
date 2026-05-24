from __future__ import annotations

import os
import requests
import streamlit as st
import folium
from streamlit_folium import st_folium


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="Factory Placement", layout="wide")

st.title("Размещение завода: подбор площадки (MVP по ТЗ)")

with st.sidebar:
    st.header("Параметры инвестора (10 полей)")

    # 3.1 Производство (4 поля в ТЗ, но три числовых + утеплитель)
    volume = st.slider("Объем выпуска (тыс. м²/год)", 100, 1000, 300, 50)
    employees = st.slider("Количество сотрудников", 10, 200, 80, 5)
    budget = st.slider("Бюджет на участок и сети (млн руб)", 10, 300, 120, 10)
    insulation_type = st.selectbox("Тип утеплителя", ["ppu", "minvata", "pps"], index=0)

    # 3.2 Логистика (2)
    needs_railway = st.toggle("Необходима ж/д ветка", value=False)
    max_dist_highway = st.slider("Макс. расстояние до федеральной трассы (км)", 1, 100, 20, 1)

    # 3.3 Архитектура и стиль (2)
    arch = st.selectbox(
        "Архитектурный приоритет",
        ["authentic", "techno", "eco"],
        format_func={"authentic": "Аутентичность", "techno": "Техно", "eco": "Экодизайн"}.get,
    )

    landscaping = st.multiselect(
        "Благоустройство (до 3)",
        [
            ("alley", "Аллея"),
            ("fountain_square", "Сквер с фонтаном"),
            ("gazebos", "Беседки"),
            ("stage", "Сцена"),
            ("health_trail", "Тропа здоровья"),
            ("pond", "Пруд"),
            ("art_object", "Арт-объект"),
        ],
        default=[("alley", "Аллея")],
        max_selections=3,
        format_func=lambda x: x[1],
    )

    # 3.4 Социальные приоритеты (3)
    housing_share = st.select_slider("Жилье сотрудникам (%)", options=[0, 30, 50, 70], value=30)
    housing_type = st.selectbox("Тип жилья", ["none", "dorm", "apartments"], index=1)

    kinder = st.select_slider("Детсад: мест на 100 сотрудников", options=[0, 15, 30, 50], value=15)

    sports = st.multiselect(
        "Спорт (до 2)",
        [
            ("street_gym", "Уличные тренажёры"),
            ("stadium", "Стадион"),
            ("pool", "Бассейн"),
            ("gym", "Спортзал"),
            ("hockey", "Хоккейная коробка"),
        ],
        default=[("street_gym", "Уличные тренажёры")],
        max_selections=2,
        format_func=lambda x: x[1],
    )

    st.divider()
    st.caption("LLM (опционально)")
    gemini_api_key = st.text_input("Gemini API key", type="password")

    run = st.button("Найти участок")

col1, col2 = st.columns([0.55, 0.45])

with col1:
    st.subheader("Карта")

    if "marker_location" not in st.session_state:
        st.session_state.marker_location = [55.75, 37.62]

    m = folium.Map(location=st.session_state.marker_location, zoom_start=5)

    map_output = st_folium(m, height=520, returned_objects=["last_clicked"])
    if map_output and map_output.get("last_clicked"):
        st.session_state.marker_location = [
            map_output["last_clicked"]["lat"],
            map_output["last_clicked"]["lng"],
        ]

with col2:
    st.subheader("Результаты")

    if run:
        payload = {
            "volume_k_sqm_per_year": float(volume),
            "employees": int(employees),
            "budget_m_rub": float(budget),
            "insulation_type": insulation_type,
            "needs_railway": bool(needs_railway),
            "max_distance_to_highway_km": float(max_dist_highway),
            "architecture_priority": arch,
            "landscaping": [x[0] for x in landscaping],
            "housing_share_pct": int(housing_share),
            "housing_type": housing_type,
            "kindergarten_places_per_100": int(kinder),
            "sports": [x[0] for x in sports],
            "gemini_api_key": gemini_api_key or None,
        }

        try:
            resp = requests.post(f"{API_BASE_URL}/v1/evaluate", json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()

            st.write("**ТОП-3 региона:**")
            for i, r in enumerate(data["ranking"], start=1):
                st.write(f"{i}. {r['region_name']} — score={r['score']:.3f}")
                for reason in r.get("reasons", []):
                    st.caption(f"- {reason}")

            st.divider()
            st.write("**Площади (м², формулы из ТЗ):**")
            st.json(data["areas"])

            st.divider()
            st.write("**Смета (руб, нормативы из ТЗ):**")
            st.json(data["costs"])

            st.divider()
            st.write("**Аналитическая справка (Markdown):**")
            st.markdown(data.get("report_md") or "")

        except Exception as e:
            st.error(f"Ошибка запроса к API: {e}")
