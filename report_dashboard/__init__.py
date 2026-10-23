import pandas as pd
import streamlit as st

from report_dashboard.charts import render_charts
from report_dashboard.filters import apply_filters, render_filters
from report_dashboard.indicators import render_indicators
from report_dashboard.tables import render_tables


def render_dashboard(data: pd.DataFrame) -> None:
    st.caption(
        "Acompanhamento de relatórios de qualificação sincronizados com o OneDrive."
    )

    filtered_data = apply_filters(data, render_filters(data))
    if filtered_data.empty:
        st.info("Nenhum relatório corresponde aos filtros selecionados.")
        return

    render_indicators(filtered_data)
    render_charts(filtered_data)
    render_tables(filtered_data)
