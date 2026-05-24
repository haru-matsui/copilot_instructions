from __future__ import annotations

import os
import requests
import streamlit as st
import folium
from streamlit_folium import st_folium


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="Factory Placement", layout="wide")

st.title("Размещение завода: подбор площадки (MVP)")

with st.sidebar:
    st.header("Параметры инвестора")

    volume = st.slider("Объем выпуска (тыс. м²/год)", 100, 1000, 300, 50)
    employees = st.slider("Сотрудники (чел)", 10, 200, 80, 5)
    budget = st.slider("Бюджет (млн руб)", 50, 5000, 800, 50)

    needs_railway = st.toggle("Нужна ж/д ветка", value=False)
    max_dist_highway = st.slider("Макс. расстояние до трассы (км)", 1, 100, 20, 1)

    arch = st.selectbox(
        "Архитектурный приоритет",
        ["authentic", "techno", "eco"],
        format_func={"authentic": "Аутентичность", "techno": "Техно", "eco": "Эко"}.get,
    )
    landscaping = st.slider("Благоустройство (вес)", 0, 100, 50, 5)

    housing_share = st.select_slider("Жилье сотрудникам (%)", options=[0, 30, 50, 70], value=30)
    housing_type = st.selectbox("Тип жилья", ["none", "dorm", "apartments"], index=1)

    kinder = st.slider("Детсад: мест на 100 сотрудников", 0, 100, 20, 5)

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
            "needs_railway": bool(needs_railway),
            "max_distance_to_highway_km": float(max_dist_highway),
            "architecture_priority": arch,
            "landscaping_level": int(landscaping),
            "housing_share_pct": int(housing_share),
            "housing_type": housing_type,
            "kindergarten_places_per_100": int(kinder),
        }

        try:
            resp = requests.post(f"{API_BASE_URL}/v1/evaluate", json=payload, timeout=20)
            resp.raise_for_status()
            data = resp.json()

            st.write("**ТОП-3 региона:**")
            for i, r in enumerate(data["ranking"], start=1):
                st.write(f"{i}. {r['region_name']} — score={r['score']}")
                for reason in r.get("reasons", []):
                    st.caption(f"- {reason}")

            st.divider()
            st.write("**Площади (м²):**")
            st.json(data["areas"])

            st.divider()
            st.write("**Смета (руб):**")
            st.json(data["costs"])

        except Exception as e:
            st.error(f"Ошибка запроса к API: {e}")
