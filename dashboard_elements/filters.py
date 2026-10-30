from datetime import date
from typing import Literal, TypedDict

import pandas as pd
import streamlit as st


class FilterSelection(TypedDict):
    statuses: list[str]
    clients: list[str]
    technicians: list[str]
    date_column: Literal["data_conclusao", "data_entrega"]
    date_range: tuple[date, date] | None


def render_filters(data: pd.DataFrame) -> FilterSelection:
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

        date_columns: dict[str, Literal["data_conclusao", "data_entrega"]] = {
            "Data de conclusão": "data_conclusao",
            "Data de entrega": "data_entrega",
        }
        selected_date_column = st.selectbox(
            "Data usada no período",
            options=list(date_columns.keys()),
            help=(
                "Escolha qual evento deve estar dentro do intervalo. "
                "Isso permite filtrar conclusões e entregas separadamente."
            ),
        )
        date_column: Literal["data_conclusao", "data_entrega"] = date_columns[
            selected_date_column
        ]
        date_range: tuple[date, date] | None = None
        valid_dates = data[date_column].dropna()
        if not valid_dates.empty:
            min_date = valid_dates.min().date()
            max_date = valid_dates.max().date()
            start_date = st.date_input(
                f"{selected_date_column} — início",
                value=min_date,
                min_value=min_date,
                max_value=max_date,
                format="DD/MM/YYYY",
            )
            end_date = st.date_input(
                f"{selected_date_column} — fim",
                value=max_date,
                min_value=min_date,
                max_value=max_date,
                format="DD/MM/YYYY",
            )
            if isinstance(start_date, date) and isinstance(end_date, date):
                date_range = (start_date, end_date)

    return {
        "statuses": selected_statuses,
        "clients": selected_clients,
        "technicians": selected_technicians,
        "date_column": date_column,
        "date_range": date_range,
    }


def apply_filters(
    data: pd.DataFrame,
    filters: FilterSelection,
) -> pd.DataFrame:
    filtered_data = data[
        data["status"].isin(filters["statuses"])
        & data["cliente"].isin(filters["clients"])
        & data["tecnico"].isin(filters["technicians"])
    ].copy()

    date_range = filters["date_range"]
    if date_range:
        start_date, end_date = date_range
        event_dates = filtered_data[filters["date_column"]].dt.date
        filtered_data = filtered_data[
            event_dates.ge(start_date) & event_dates.le(end_date)
        ]

    return filtered_data
