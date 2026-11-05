import pandas as pd
import streamlit as st


def render_charts(data: pd.DataFrame) -> None:
    st.divider()
    monthly_column, client_column = st.columns(2)

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
            st.bar_chart(
                top_clients.to_frame(),
                sort="-Relatórios",
                horizontal=True,
            )

    st.subheader("Relatórios por técnico")
    technician_counts = (
        data["tecnico"].dropna().value_counts().rename("Relatórios")
    )
    if technician_counts.empty:
        st.info("Não há técnicos para exibir.")
    else:
        technician_table = (
            technician_counts.rename_axis("Técnico")
            .reset_index()
            .sort_values("Relatórios", ascending=False)
        )
        st.dataframe(
            technician_table,
            width="stretch",
            hide_index=True,
            alt="Quantidade de relatórios atribuídos a cada técnico",
        )
