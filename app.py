from datetime import timedelta

import requests
import streamlit as st

from dashboard_elements import render_dashboard
from dashboard_elements.detailed_analytics import render_detailed_analytics
from dashboard_elements.data import (
    DATA_CACHE_TTL_SECONDS,
    load_data_from_onedrive,
    prepare_report_data,
)
from dashboard_elements.filters import apply_filters, render_filters


st.set_page_config(
    page_title="Controle de Relatórios",
    page_icon="📊",
    layout="wide",
)
st.markdown(
    """
    <style>
    .stApp {
        background: transparent;
    }

    .stApp::before {
        content: "";
        position: fixed;
        inset: 0;
        z-index: 0;
        pointer-events: none;
        opacity: 0.03;
        background:
            linear-gradient(rgba(255, 255, 255, 0.12), rgba(255, 255, 255, 0.12)),
            url("/app/static/laboratory-background.jpg") center / cover no-repeat;
    }

    .stApp > header,
    .stApp > div {
        position: relative;
        z-index: 1;
    }

    [data-testid="stAppViewContainer"] {
        background: transparent;
    }

    [data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.92);
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("Dashboard: Controle de Relatórios")

with st.sidebar:
    selected_page = st.radio(
        "Página",
        options=["Visão geral", "Análises detalhadas"],
    )
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
    elif selected_page == "Visão geral":
        st.header("Visão geral")
        render_dashboard(report_data)
    else:
        st.header("Análises detalhadas")
        st.caption(
            "Explore o volume mensal de serviços técnicos concluídos e o tempo "
            "entre a conclusão técnica e a entrega do relatório."
        )
        filters = render_filters(report_data)
        filtered_data = apply_filters(report_data, filters)
        if filtered_data.empty:
            st.info("Nenhum relatório corresponde aos filtros selecionados.")
        else:
            render_detailed_analytics(filtered_data)


render_dashboard_page()
