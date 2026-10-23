import pandas as pd
import streamlit as st

from dashboard_elements.charts import render_charts
from dashboard_elements.filters import apply_filters, render_filters
from dashboard_elements.indicators import render_indicators
from dashboard_elements.tables import render_tables


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
