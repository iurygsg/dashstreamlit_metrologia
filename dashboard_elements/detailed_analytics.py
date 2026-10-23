import altair as alt
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
        "A contagem usa “Data de conclusão” como aproximação e mostra os serviços "
        "técnicos concluídos em cada mês; não representa necessariamente quando "
        "as tarefas entraram."
    )
    completed_services = analysis_data.dropna(subset=["data_conclusao"]).copy()
    if completed_services.empty:
        st.info("Não há datas de conclusão para agrupar por mês.")
    else:
        completed_services["Mês"] = (
            completed_services["data_conclusao"].dt.to_period("M").dt.to_timestamp()
        )
        monthly_counts = (
            completed_services.groupby("Mês")
            .size()
            .rename("Serviços técnicos concluídos")
        )
        st.line_chart(monthly_counts.to_frame())

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
        monthly_medians_data = monthly_medians.rename_axis("Mês").reset_index()
        month_labels = {
            1: "jan",
            2: "fev",
            3: "mar",
            4: "abr",
            5: "mai",
            6: "jun",
            7: "jul",
            8: "ago",
            9: "set",
            10: "out",
            11: "nov",
            12: "dez",
        }
        monthly_medians_data["Mês"] = (
            monthly_medians_data["Mês"].dt.month.map(month_labels)
            + "/"
            + monthly_medians_data["Mês"].dt.year.astype(str)
        )
        month_order = monthly_medians_data["Mês"].tolist()
        monthly_medians_chart = (
            alt.Chart(monthly_medians_data)
            .mark_line(point=True)
            .encode(
                x=alt.X(
                    "Mês:N",
                    sort=month_order,
                    axis=alt.Axis(
                        title=None,
                        labelAngle=-45,
                        labelOverlap=True,
                    ),
                ),
                y=alt.Y(
                    "dias_producao:Q",
                    title="Dias",
                ),
                tooltip=[
                    alt.Tooltip("Mês:N", title="Mês"),
                    alt.Tooltip(
                        "dias_producao:Q",
                        title="Mediana (dias)",
                        format=".1f",
                    ),
                ],
            )
            .properties(height=350)
        )
        st.altair_chart(monthly_medians_chart, width="stretch")

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
