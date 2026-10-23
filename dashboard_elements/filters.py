from datetime import date

import pandas as pd
import streamlit as st


def render_filters(data: pd.DataFrame) -> dict[str, object]:
    with st.sidebar:
        st.header("Filtros")
        selected_statuses = st.multiselect(
            "Status",
            options=sorted(data["status"].dropna().unique().tolist()),
            default=sorted(data["status"].dropna().unique().tolist()),
        )

        clients = sorted(data["cliente"].dropna().unique().tolist())
        selected_clients = st.multiselect(
            "Cliente",
            options=clients,
            default=clients,
        )

        technicians = sorted(data["tecnico"].dropna().unique().tolist())
        selected_technicians = st.multiselect(
            "Técnico",
            options=technicians,
            default=technicians,
        )

        date_range: tuple[date, date] | None = None
        valid_dates = data["data_conclusao"].dropna()
        if not valid_dates.empty:
            min_date = valid_dates.min().date()
            max_date = valid_dates.max().date()
            selected_dates = st.date_input(
                "Data de conclusão",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                format="DD/MM/YYYY",
            )
            if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
                date_range = (selected_dates[0], selected_dates[1])

    return {
        "statuses": selected_statuses,
        "clients": selected_clients,
        "technicians": selected_technicians,
        "date_range": date_range,
    }


def apply_filters(
    data: pd.DataFrame,
    filters: dict[str, object],
) -> pd.DataFrame:
    filtered_data = data[
        data["status"].isin(filters["statuses"])
        & data["cliente"].isin(filters["clients"])
        & data["tecnico"].isin(filters["technicians"])
    ].copy()

    date_range = filters["date_range"]
    if date_range:
        start_date, end_date = date_range
        completion_dates = filtered_data["data_conclusao"].dt.date
        filtered_data = filtered_data[
            completion_dates.ge(start_date) & completion_dates.le(end_date)
        ]

    return filtered_data
