import pandas as pd
import streamlit as st


def render_detailed_analytics(data: pd.DataFrame) -> None:
    analysis_data = data.copy()
    analysis_data["dias_producao"] = (
        analysis_data["data_entrega"] - analysis_data["data_conclusao"]
    ).dt.days

    valid_production = analysis_data[
        analysis_data["dias_producao"].notna()
        & analysis_data["dias_producao"].ge(0)
    ].copy()
    invalid_duration_count = int(
        (
            analysis_data["data_entrega"].notna()
            & analysis_data["data_conclusao"].notna()
            & analysis_data["dias_producao"].lt(0)
        ).sum()
    )

    st.subheader("Tempo de produção do relatório")
    metrics = st.columns(3)
    if valid_production.empty:
        metrics[0].metric("Mediana até a entrega", "Sem dados")
        metrics[1].metric("Média até a entrega", "Sem dados")
    else:
        metrics[0].metric(
            "Mediana até a entrega",
            f"{valid_production['dias_producao'].median():.0f} dias",
        )
        metrics[1].metric(
            "Média até a entrega",
            f"{valid_production['dias_producao'].mean():.1f} dias",
        )
    metrics[2].metric("Relatórios com datas válidas", f"{len(valid_production):,}")
    st.caption(
        "O prazo é calculado em dias corridos entre a conclusão do serviço técnico "
        "e a entrega do relatório. Só entram no cálculo registros com as duas "
        "datas preenchidas e a entrega na mesma data ou depois da conclusão."
    )
    if invalid_duration_count:
        st.warning(
            f"{invalid_duration_count} registro(s) com entrega anterior à conclusão "
            "foram excluídos do cálculo do prazo."
        )

    st.divider()
    st.subheader("Tarefas por mês")
    st.caption(
        "A primeira linha mostra os serviços técnicos concluídos por mês, usando "
        "“Data de conclusão” como aproximação das entradas em produção. A segunda "
        "mostra os relatórios entregues por mês, pela “Data de entrega do relatório”."
    )
    completed_services = analysis_data.dropna(subset=["data_conclusao"]).copy()
    delivered_reports = analysis_data.dropna(subset=["data_entrega"]).copy()
    if completed_services.empty and delivered_reports.empty:
        st.info("Não há datas de conclusão ou de entrega para agrupar por mês.")
    else:
        completed_counts = (
            completed_services["data_conclusao"]
            .dt.to_period("M")
            .value_counts()
            .rename("Serviços técnicos concluídos")
        )
        delivered_counts = (
            delivered_reports["data_entrega"]
            .dt.to_period("M")
            .value_counts()
            .rename("Relatórios entregues")
        )
        monthly_counts = pd.concat(
            [completed_counts, delivered_counts], axis=1
        ).fillna(0)
        monthly_counts = monthly_counts.astype(int).sort_index()
        monthly_counts.index = monthly_counts.index.to_timestamp()
        monthly_counts = monthly_counts.asfreq("MS", fill_value=0)
        st.line_chart(
            monthly_counts,
            y=list(monthly_counts.columns),
            color=["#2563EB", "#14B8A6"],
        )

    monthly_production = valid_production.dropna(subset=["data_conclusao"]).copy()
    if monthly_production.empty:
        st.info("Não há prazos válidos para calcular a mediana mensal.")
    else:
        monthly_production["Mês"] = (
            monthly_production["data_conclusao"]
            .dt.to_period("M")
            .dt.to_timestamp()
        )
        monthly_medians = (
            monthly_production.groupby("Mês")["dias_producao"]
            .median()
            .rename("Mediana até a entrega (dias)")
        )
        st.subheader("Mediana do tempo de produção por mês")
        st.caption("Tempo que leva para a produção do relatório")
        st.line_chart(monthly_medians.to_frame())

    with st.expander("Ver prazos por relatório"):
        report_details = valid_production[
            [
                "status",
                "tarefa",
                "cliente",
                "tecnico",
                "data_conclusao",
                "data_entrega",
                "dias_producao",
            ]
        ].rename(
            columns={
                "status": "Status",
                "tarefa": "Tarefa",
                "cliente": "Cliente",
                "tecnico": "Técnico",
                "data_conclusao": "Conclusão do serviço técnico",
                "data_entrega": "Entrega do relatório",
                "dias_producao": "Dias de produção",
            }
        )
        report_details = report_details.sort_values(
            "Dias de produção", ascending=False
        )
        for column in ("Conclusão do serviço técnico", "Entrega do relatório"):
            report_details[column] = pd.to_datetime(
                report_details[column]
            ).dt.strftime("%d/%m/%Y")
        st.dataframe(report_details, width="stretch", hide_index=True)
