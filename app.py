from datetime import timedelta

import requests
import streamlit as st

from dashboard_elements import render_dashboard
from dashboard_elements.data import (
    DATA_CACHE_TTL_SECONDS,
    load_data_from_onedrive,
    prepare_report_data,
)


st.set_page_config(
    page_title="Controle de Relatórios",
    page_icon="📊",
    layout="wide",
)
st.title("Dashboard: Controle de Relatórios")

with st.sidebar:
    st.button(
        "Atualizar dados agora",
        on_click=load_data_from_onedrive.clear,
        help="Descarta o cache e busca a planilha do OneDrive novamente.",
    )
    st.caption("Atualização automática a cada hora.")


@st.fragment(run_every=timedelta(seconds=DATA_CACHE_TTL_SECONDS))
def render_dashboard_page() -> None:
    try:
        raw_data = load_data_from_onedrive()
    except requests.RequestException as error:
        st.error(f"Falha ao baixar a planilha do OneDrive: {error}")
        return
    except RuntimeError as error:
        st.error(str(error))
        return

    try:
        report_data = prepare_report_data(raw_data)
    except ValueError as error:
        st.error(f"Não foi possível interpretar a planilha: {error}")
        return

    if report_data.empty:
        st.warning("A planilha não contém relatórios para exibir.")
    else:
        render_dashboard(report_data)


render_dashboard_page()
