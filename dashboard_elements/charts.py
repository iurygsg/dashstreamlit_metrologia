import pandas as pd
import streamlit as st


def render_charts(data: pd.DataFrame) -> None:
    st.divider()
    status_column, monthly_column = st.columns(2)

    with status_column:
        st.subheader("Relatórios por status")
        status_counts = data["status"].value_counts().rename("Relatórios")
        st.bar_chart(status_counts.to_frame(), sort="-Relatórios")

    with monthly_column:
        st.subheader("Conclusões por mês")
        monthly_data = data.dropna(subset=["data_conclusao"]).copy()
        if monthly_data.empty:
            st.info("Não há datas de conclusão para exibir.")
        else:
            monthly_data["Mês"] = (
                monthly_data["data_conclusao"].dt.to_period("M").dt.to_timestamp()
            )
            monthly_counts = (
                monthly_data.groupby("Mês").size().rename("Relatórios concluídos")
            )
            st.line_chart(monthly_counts.to_frame())

    client_column, technician_column = st.columns(2)
    with client_column:
        st.subheader("Clientes com mais relatórios")
        top_clients = (
            data["cliente"]
            .dropna()
            .value_counts()
            .head(10)
            .rename("Relatórios")
        )
        if top_clients.empty:
            st.info("Não há clientes para exibir.")
        else:
            st.bar_chart(top_clients.to_frame(), sort="-Relatórios")

    with technician_column:
        st.subheader("Relatórios por técnico")
        technician_counts = (
            data["tecnico"].dropna().value_counts().rename("Relatórios")
        )
        if technician_counts.empty:
            st.info("Não há técnicos para exibir.")
        else:
            st.bar_chart(technician_counts.to_frame(), sort="-Relatórios")
