import pandas as pd
import streamlit as st


def render_tables(data: pd.DataFrame) -> None:
    render_overdue_reports(data)
    render_filtered_reports(data)


def render_overdue_reports(data: pd.DataFrame) -> None:
    overdue_reports = data[data["status"].eq("Em atraso")].copy()
    if overdue_reports.empty:
        return

    st.subheader("Acompanhamento de atrasos")
    overdue_days = overdue_reports["dias_atraso"].dropna()
    if not overdue_days.empty:
        st.caption(
            "Atraso mediano: "
            f"{overdue_days.median():.0f} dias · "
            f"maior atraso: {overdue_days.max():.0f} dias"
        )

    overdue_reports = overdue_reports.sort_values(
        "dias_atraso", ascending=False, na_position="last"
    )
    overdue_table = overdue_reports[
        [
            "tarefa",
            "cliente",
            "equipamento",
            "tecnico",
            "dias_atraso",
            "data_conclusao",
        ]
    ].rename(
        columns={
            "tarefa": "Tarefa",
            "cliente": "Cliente",
            "equipamento": "Equipamento",
            "tecnico": "Técnico",
            "dias_atraso": "Dias em atraso",
            "data_conclusao": "Data de conclusão",
        }
    )
    overdue_table["Data de conclusão"] = pd.to_datetime(
        overdue_table["Data de conclusão"]
    ).dt.strftime("%d/%m/%Y")
    st.dataframe(overdue_table, width="stretch", hide_index=True)


def render_filtered_reports(data: pd.DataFrame) -> None:
    with st.expander("Ver relatórios filtrados"):
        table = data[
            [
                "status",
                "tarefa",
                "data_conclusao",
                "cliente",
                "equipamento",
                "tecnico",
                "dias_atraso",
                "data_entrega",
                "responsavel",
                "observacao",
            ]
        ].rename(
            columns={
                "status": "Status",
                "tarefa": "Tarefa",
                "data_conclusao": "Data de conclusão",
                "cliente": "Cliente",
                "equipamento": "Equipamento",
                "tecnico": "Técnico",
                "dias_atraso": "Dias em atraso",
                "data_entrega": "Data de entrega",
                "responsavel": "Responsável pela liberação",
                "observacao": "Observação",
            }
        )
        for column in ("Data de conclusão", "Data de entrega"):
            table[column] = pd.to_datetime(table[column]).dt.strftime("%d/%m/%Y")
        st.dataframe(table, width="stretch", hide_index=True)
