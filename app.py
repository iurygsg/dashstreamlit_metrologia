import requests
import streamlit as st

from dashboard_elements import render_dashboard
from dashboard_elements.data import load_data_from_onedrive, prepare_report_data


st.set_page_config(
    page_title="Controle de Relatórios",
    page_icon="📊",
    layout="wide",
)
st.title("Dashboard: Controle de Relatórios")

try:
    raw_data = load_data_from_onedrive()
except requests.RequestException as error:
    st.error(f"Falha ao baixar a planilha do OneDrive: {error}")
    st.stop()
except RuntimeError as error:
    st.error(str(error))
    st.stop()

try:
    report_data = prepare_report_data(raw_data)
except ValueError as error:
    st.error(f"Não foi possível interpretar a planilha: {error}")
    st.stop()

if report_data.empty:
    st.warning("A planilha não contém relatórios para exibir.")
else:
    render_dashboard(report_data)
