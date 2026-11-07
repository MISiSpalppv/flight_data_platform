import pandas as pd
import plotly.express as px
import streamlit as st

from agent import OLLAMA_MODEL, ask
from lake import MARTS, available_marts, connect

st.set_page_config(page_title="Flight Data Platform", page_icon="✈", layout="wide")


@st.cache_data(ttl=60, show_spinner="Читаю витрины из lakehouse...")
def load_marts():
    return available_marts()


marts = load_marts()

st.title("Flight Data Platform")
st.caption("Воздушное движение в реальном времени: ADS-B → Kafka → Spark → Delta Lake → витрины")

if st.sidebar.button("Обновить данные"):
    load_marts.clear()
    st.rerun()
st.sidebar.markdown("**Витрины в gold**")
for name in MARTS:
    st.sidebar.write(("✅ " if name in marts else "⏳ ") + name)

if not marts:
    st.warning("Витрины ещё не построены. Дождитесь выполнения DAG flights_lakehouse_pipeline в Airflow.")
    st.stop()

tab_dash, tab_agent = st.tabs(["Дашборд", "ИИ-агент"])

with tab_dash:
    live = marts.get("mart_live_aircraft", pd.DataFrame())
    traffic = marts.get("mart_traffic_region_hour", pd.DataFrame())

    c1, c2, c3, c4 = st.columns(4)
    if not live.empty:
        airborne = live[~live["on_ground"]]
        c1.metric("Самолётов в воздухе", f"{len(airborne):,}")
        c2.metric("На земле", f"{int(live['on_ground'].sum()):,}")
        c3.metric("Средняя высота, ft", f"{airborne['altitude_ft'].mean():,.0f}")
        c4.metric("Средняя скорость, kt", f"{airborne['speed_kt'].mean():,.0f}")

        st.subheader("Карта самолётов")
        fig = px.scatter_map(
            airborne.dropna(subset=["lat", "lon"]),
            lat="lat", lon="lon", color="altitude_ft", color_continuous_scale="Turbo",
            hover_name="callsign", hover_data=["aircraft_type", "altitude_ft", "speed_kt", "region"],
            zoom=2, height=560, map_style="open-street-map",
        )
        fig.update_traces(marker={"size": 6})
        fig.update_layout(margin={"l": 0, "r": 0, "t": 0, "b": 0})
        st.plotly_chart(fig, use_container_width=True)

    left, right = st.columns(2)
    if not traffic.empty:
        with left:
            st.subheader("Трафик по регионам")
            fig = px.line(traffic.sort_values("hour"), x="hour", y="unique_aircraft", color="region", markers=True)
            st.plotly_chart(fig, use_container_width=True)
    types = marts.get("mart_aircraft_types")
    if types is not None and not types.empty:
        with right:
            st.subheader("Популярные типы самолётов")
            top = types.sort_values("unique_aircraft", ascending=False).head(12)
            st.plotly_chart(px.bar(top, x="aircraft_type", y="unique_aircraft"), use_container_width=True)

    left, right = st.columns(2)
    airlines = marts.get("mart_airline_activity")
    if airlines is not None and not airlines.empty:
        with left:
            st.subheader("Топ авиакомпаний по числу бортов")
            top = airlines.groupby("airline_code", as_index=False)["unique_aircraft"].max().nlargest(12, "unique_aircraft")
            st.plotly_chart(px.bar(top, x="airline_code", y="unique_aircraft"), use_container_width=True)
    airports = marts.get("mart_airport_activity")
    if airports is not None and not airports.empty:
        with right:
            st.subheader("Самые загруженные аэропорты")
            top = airports.groupby(["iata", "name"], as_index=False)["unique_aircraft"].max().nlargest(12, "unique_aircraft")
            st.plotly_chart(px.bar(top, x="iata", y="unique_aircraft", hover_data=["name"]), use_container_width=True)

    emergencies = marts.get("mart_emergency_events")
    if emergencies is not None and not emergencies.empty:
        st.subheader("Аварийные сигналы")
        st.dataframe(emergencies.sort_values("position_ts", ascending=False).head(50), use_container_width=True)

with tab_agent:
    st.write(f"Агент отвечает на вопросы, строя SQL-запросы к витринам gold. Модель: `{OLLAMA_MODEL}` (локально, Ollama).")
    examples = [
        "Сколько сейчас самолётов в воздухе по каждому региону?",
        "Какие 5 типов самолётов встречаются чаще всего?",
        "Какой самый загруженный аэропорт?",
        "Были ли аварийные сигналы?",
    ]
    cols = st.columns(len(examples))
    clicked = None
    for col, example in zip(cols, examples):
        if col.button(example):
            clicked = example

    if "history" not in st.session_state:
        st.session_state.history = []
    for item in st.session_state.history:
        with st.chat_message(item["role"]):
            st.markdown(item["content"])
            if item.get("sql"):
                with st.expander("SQL-запрос"):
                    st.code(item["sql"], language="sql")
            if item.get("data") is not None:
                st.dataframe(item["data"], use_container_width=True)

    question = st.chat_input("Задайте вопрос о воздушном движении") or clicked
    if question:
        st.session_state.history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Агент анализирует витрины..."):
                try:
                    result = ask(question, connect(marts), marts)
                    st.markdown(result["answer"])
                    with st.expander("SQL-запрос"):
                        st.code(result["sql"], language="sql")
                    if result["data"] is not None:
                        st.dataframe(result["data"], use_container_width=True)
                    st.session_state.history.append(
                        {"role": "assistant", "content": result["answer"], "sql": result["sql"], "data": result["data"]}
                    )
                except Exception as exc:
                    st.error(f"Ошибка обращения к модели: {exc}")
