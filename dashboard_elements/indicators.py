import pandas as pd
import streamlit as st


def render_indicators(data: pd.DataFrame) -> None:
    delivered = int(data["status"].eq("Entregue").sum())
    overdue = int(data["status"].eq("Em atraso").sum())
    cancelled = int(data["status"].eq("Cancelado").sum())

    active_reports = len(data) - cancelled
    delivery_rate = delivered / active_reports * 100 if active_reports else 0
    metrics = st.columns(5)
    metrics[0].metric("Relatórios", f"{len(data):,}".replace(",", "."))
    metrics[1].metric("Entregues", f"{delivered:,}".replace(",", "."))
    metrics[2].metric(
        "Taxa entregue",
        f"{delivery_rate:.1f}%",
        help="Percentual dos relatórios não cancelados que foram entregues.",
    )
    metrics[3].metric("Em atraso", f"{overdue:,}".replace(",", "."))
    metrics[4].metric("Cancelados", f"{cancelled:,}".replace(",", "."))
