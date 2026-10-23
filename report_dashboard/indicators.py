import pandas as pd
import streamlit as st


def render_indicators(data: pd.DataFrame) -> None:
    delivered = int(data["status"].eq("Entregue").sum())
    overdue = int(data["status"].eq("Em atraso").sum())
    cancelled = int(data["status"].eq("Cancelado").sum())

    delivered_reports = data[
        data["status"].eq("Entregue")
        & data["data_entrega"].notna()
        & data["data_conclusao"].notna()
    ]
    delivery_days = (
        delivered_reports["data_entrega"] - delivered_reports["data_conclusao"]
    ).dt.days
    delivery_days = delivery_days[delivery_days.ge(0)]

    active_reports = len(data) - cancelled
    delivery_rate = delivered / active_reports * 100 if active_reports else 0
    metrics = st.columns(6)
    metrics[0].metric("Relatórios", f"{len(data):,}".replace(",", "."))
    metrics[1].metric("Entregues", f"{delivered:,}".replace(",", "."))
    metrics[2].metric(
        "Taxa entregue",
        f"{delivery_rate:.1f}%",
        help="Percentual dos relatórios não cancelados que foram entregues.",
    )
    metrics[3].metric("Em atraso", f"{overdue:,}".replace(",", "."))
    metrics[4].metric("Cancelados", f"{cancelled:,}".replace(",", "."))

    if delivery_days.empty:
        metrics[5].metric("Mediana até entrega", "Sem dados")
    else:
        metrics[5].metric(
            "Mediana até entrega",
            f"{delivery_days.median():.0f} dias",
            help=(
                "Calculada com "
                f"{len(delivery_days)} relatórios entregues com datas válidas."
            ),
        )
