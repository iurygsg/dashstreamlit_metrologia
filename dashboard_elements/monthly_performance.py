from numbers import Real

import pandas as pd
import streamlit as st


COMPLETED_SERVICES = "Serviços técnicos concluídos"
DELIVERED_REPORTS = "Relatórios entregues"
MEDIAN_DELIVERY_DAYS = "Mediana até a entrega (dias)"
MONTH_NAMES = (
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
)


def build_monthly_metrics(
    data: pd.DataFrame,
    months: pd.DatetimeIndex,
) -> pd.DataFrame:
    monthly = pd.DataFrame(index=months)

    completed_months = (
        data["data_conclusao"]
        .dropna()
        .dt.to_period("M")
        .dt.to_timestamp()
        .value_counts()
    )
    delivered_months = (
        data["data_entrega"]
        .dropna()
        .dt.to_period("M")
        .dt.to_timestamp()
        .value_counts()
    )
    monthly[COMPLETED_SERVICES] = completed_months.reindex(months, fill_value=0)
    monthly[DELIVERED_REPORTS] = delivered_months.reindex(months, fill_value=0)

    production_days = (
        data["data_entrega"] - data["data_conclusao"]
    ).dt.days
    valid_delivery = data["data_entrega"].notna() & production_days.ge(0)
    median_by_delivery_month = (
        data.loc[valid_delivery]
        .assign(
            dias_producao=production_days.loc[valid_delivery],
            mes_entrega=(
                data.loc[valid_delivery, "data_entrega"]
                .dt.to_period("M")
                .dt.to_timestamp()
            ),
        )
        .groupby("mes_entrega")["dias_producao"]
        .median()
    )
    monthly[MEDIAN_DELIVERY_DAYS] = median_by_delivery_month.reindex(months)
    return monthly


def _month_offset(month: pd.Timestamp, offset: int) -> pd.Timestamp:
    absolute_month = month.year * 12 + month.month - 1 + offset
    return pd.Timestamp(
        year=absolute_month // 12,
        month=absolute_month % 12 + 1,
        day=1,
    )


def _numeric_cell(
    monthly_metrics: pd.DataFrame,
    month: pd.Timestamp,
    metric: str,
) -> float | None:
    value = monthly_metrics.loc[month, metric]
    if not isinstance(value, Real):
        return None
    numeric_value = float(value)
    return None if pd.isna(numeric_value) else numeric_value


def _comparison_value(
    monthly_metrics: pd.DataFrame,
    month: pd.Timestamp,
    metric: str,
    comparison: str,
    first_data_month: pd.Timestamp,
) -> float | None:
    if comparison == "Mês anterior":
        baseline_month = _month_offset(month, -1)
        if baseline_month < first_data_month:
            return None
        return _numeric_cell(monthly_metrics, baseline_month, metric)

    baseline_months = pd.date_range(
        _month_offset(month, -3),
        _month_offset(month, -1),
        freq="MS",
    )
    if baseline_months[0] < first_data_month:
        return None

    baseline = monthly_metrics.loc[baseline_months, metric].dropna()
    if baseline.empty:
        return None
    mean_value = baseline.mean()
    return float(mean_value) if isinstance(mean_value, Real) else None


def _format_delta(value: float, baseline: float | None) -> str:
    if baseline is None or pd.isna(baseline):
        return "Sem base de comparação"

    difference = value - baseline
    if difference == 0:
        return "Sem variação"

    difference_label = f"{difference:+.1f}".replace(".", ",")
    if baseline == 0:
        return difference_label

    percentage = difference / baseline * 100
    percentage_label = f"{percentage:+.1f}%".replace(".", ",")
    return f"{difference_label} ({percentage_label})"


def _render_metric(
    label: str,
    value: float | None,
    baseline: float | None,
    *,
    unit: str = "",
    inverse: bool = False,
) -> None:
    if value is None or pd.isna(value):
        st.metric(label, "Sem dados", delta="Sem base de comparação", delta_color="off")
        return

    formatted_value = (
        f"{value:.0f}{unit}" if unit else f"{value:,.0f}".replace(",", ".")
    )
    st.metric(
        label,
        formatted_value,
        delta=_format_delta(value, baseline),
        delta_color="inverse" if inverse else "normal",
    )


def render_monthly_performance(data: pd.DataFrame) -> None:
    event_dates = pd.concat(
        [data["data_conclusao"], data["data_entrega"]], ignore_index=True
    ).dropna()
    if event_dates.empty:
        st.info("Não há datas de conclusão ou entrega para montar o desempenho mensal.")
        return

    event_months = event_dates.dt.to_period("M").dt.to_timestamp()
    first_data_month = event_months.min()
    last_data_month = event_months.max()
    if not isinstance(first_data_month, pd.Timestamp) or not isinstance(
        last_data_month, pd.Timestamp
    ):
        st.error("Não foi possível determinar o intervalo mensal das datas.")
        return
    current_month = pd.Timestamp.today().to_period("M").to_timestamp()
    last_data_month = max(last_data_month, current_month)
    available_months = pd.date_range(first_data_month, last_data_month, freq="MS")
    monthly_metrics = build_monthly_metrics(data, available_months)

    month_labels = {
        month: month.strftime("%m/%Y") for month in available_months
    }
    selected_label = st.selectbox(
        "Mês do retrato",
        options=list(month_labels.values()),
        index=len(available_months) - 1,
    )
    selected_month = next(
        month for month, label in month_labels.items() if label == selected_label
    )
    comparison = st.selectbox(
        "Comparar indicadores com",
        options=["Mês anterior", "Média dos 3 meses anteriores"],
    )

    st.caption(
        "Conclusões são agrupadas pela data de conclusão; entregas, pela data de "
        "entrega. O mês mais recente pode estar incompleto. A média trimestral é "
        "a média dos valores mensais disponíveis nos três meses anteriores. Os "
        "totais contam registros da planilha, não tarefas únicas."
    )
    selected_month_label = (
        f"{MONTH_NAMES[selected_month.month - 1]} de {selected_month.year}"
    )
    st.subheader(f"Desempenho em {selected_month_label}")

    metrics = [
        COMPLETED_SERVICES,
        DELIVERED_REPORTS,
        MEDIAN_DELIVERY_DAYS,
    ]
    columns = st.columns(3)
    for column, metric in zip(columns, metrics):
        baseline = _comparison_value(
            monthly_metrics,
            selected_month,
            metric,
            comparison,
            first_data_month,
        )
        value = _numeric_cell(monthly_metrics, selected_month, metric)
        if metric == MEDIAN_DELIVERY_DAYS:
            with column:
                _render_metric(
                    metric,
                    value,
                    baseline,
                    unit=" dias",
                    inverse=True,
                )
        else:
            with column:
                _render_metric(metric, value, baseline)

    st.caption(f"Variação exibida em relação a: {comparison.lower()}.")
    st.divider()
    st.subheader("Fluxo mensal")
    chart_start = max(first_data_month, _month_offset(selected_month, -5))
    chart_months = pd.date_range(chart_start, selected_month, freq="MS")
    flow = monthly_metrics.loc[
        chart_months, [COMPLETED_SERVICES, DELIVERED_REPORTS]
    ].copy()
    flow.index.name = "Mês"
    st.bar_chart(flow)

    monthly_delivery_times = monthly_metrics[MEDIAN_DELIVERY_DAYS].dropna()
    monthly_delivery_times = monthly_delivery_times.loc[
        monthly_delivery_times.index <= selected_month
    ].tail(6)
    if not monthly_delivery_times.empty:
        st.subheader("Mediana do prazo por mês de entrega")
        monthly_delivery_times.index.name = "Mês"
        st.line_chart(monthly_delivery_times.to_frame())

    current_open = int((~data["status"].isin(["Entregue", "Cancelado"])).sum())
    current_overdue = int(data["status"].eq("Em atraso").sum())
    st.divider()
    st.subheader("Pendências na situação atual")
    current_columns = st.columns(2)
    current_columns[0].metric(
        "Relatórios ainda não entregues",
        f"{current_open:,}".replace(",", "."),
    )
    current_columns[1].metric(
        "Relatórios em atraso",
        f"{current_overdue:,}".replace(",", "."),
    )
    st.caption(
        "Este é um retrato dos status atuais da planilha, não o backlog histórico "
        "no encerramento do mês selecionado."
    )
