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
    metrics = st.columns(2)
    if valid_production.empty:
        metrics[0].metric("Média até a entrega", "Sem dados")
    else:
        metrics[0].metric(
            "Média até a entrega",
            f"{valid_production['dias_producao'].mean():.1f} dias",
        )
    metrics[1].metric("Relatórios com datas válidas", f"{len(valid_production):,}")
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
    monthly_production = valid_production.dropna(subset=["data_conclusao"]).copy()
    if monthly_production.empty:
        st.info("Não há prazos válidos para calcular a média mensal.")
    else:
        monthly_production["Mês"] = (
            monthly_production["data_conclusao"]
            .dt.to_period("M")
            .dt.to_timestamp()
        )
        monthly_means = (
            monthly_production.groupby("Mês")["dias_producao"]
            .mean()
            .rename("Média até a entrega (dias)")
        )
        month_range = pd.date_range(
            monthly_means.index.min(),
            monthly_means.index.max(),
            freq="MS",
        )
        monthly_means = monthly_means.reindex(month_range)
        monthly_means.index = monthly_means.index.strftime("%m/%Y")
        st.subheader("Média do tempo de produção por mês")
        st.caption(
            "Média de dias entre a conclusão do serviço técnico e a entrega "
            "do relatório, agrupada pelo mês de conclusão."
        )
        st.line_chart(
            monthly_means.to_frame(),
            alt="Média mensal de dias entre conclusão técnica e entrega do relatório",
        )

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
