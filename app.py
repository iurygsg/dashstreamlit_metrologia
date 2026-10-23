from datetime import date
import io

import msal
import pandas as pd
import requests
import streamlit as st


st.set_page_config(
    page_title="Controle de Relatórios",
    page_icon="📊",
    layout="wide",
)

USER_EMAIL = "metrologia03@rstechengenharia.onmicrosoft.com"
FILE_PATH = "01 - DRIVE METROLOGIA/Controle de Relatórios.xlsx"
AUTHORITY = (
    "https://login.microsoftonline.com/"
    + st.secrets["microsoft"]["tenant_id"]
)
SCOPE = ["https://graph.microsoft.com/.default"]
STATUS_LABELS = {
    "ENTREGUE": "Entregue",
    "ATRASADO": "Em atraso",
    "CANCELADO": "Cancelado",
    "PENDENTE": "Pendente",
    "PENDETE": "Pendente",
    "EM REVISÃO": "Em revisão",
    "EM REVISAO": "Em revisão",
}


@st.cache_data(ttl=3600)
def load_data_from_onedrive() -> pd.DataFrame:
    client = msal.ConfidentialClientApplication(
        st.secrets["microsoft"]["client_id"],
        authority=AUTHORITY,
        client_credential=st.secrets["microsoft"]["client_secret"],
    )
    token_response = client.acquire_token_for_client(scopes=SCOPE)
    access_token = token_response.get("access_token")
    if not access_token:
        error_code = token_response.get("error", "erro desconhecido")
        raise RuntimeError(
            f"Falha na autenticação Microsoft ({error_code}). "
            "Confira as credenciais em Secrets."
        )

    url = (
        f"https://graph.microsoft.com/v1.0/users/{USER_EMAIL}"
        f"/drive/root:/{FILE_PATH}:/content"
    )
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )
    response.raise_for_status()

    return pd.read_excel(
        io.BytesIO(response.content),
        sheet_name="Planilha de Controle",
        header=2,
        usecols="B:K",
    )


def prepare_report_data(data: pd.DataFrame) -> pd.DataFrame:
    columns = {
        "RELATÓRIO DE QUALIFICAÇÃO": "status",
        "TAREFA RELACIONADA": "tarefa",
        "DATA DE CONCLUSÃO": "data_conclusao",
        "CLIENTE": "cliente",
        "EQUIPAMENTO": "equipamento",
        "OBSERVAÇÃO": "observacao",
        "TÉCNICO": "tecnico",
        "CONTAGEM DE DIAS": "dias_atraso",
        "DATA DE ENTREGA DO RELATÓRIO": "data_entrega",
        "RESPONSÁVEL PELA LIBERAÇÃO DO RELATÓRIO": "responsavel",
    }
    data = data.rename(columns=lambda column: str(column).strip())
    missing = set(columns).difference(data.columns)
    if missing:
        raise ValueError(
            "A planilha não contém todas as colunas esperadas: "
            + ", ".join(sorted(missing))
        )

    data = data.rename(columns=columns)
    data["status"] = data["status"].astype("string").str.strip().str.upper()
    data = data[data["status"].notna() & data["status"].ne("")].copy()
    data["status"] = data["status"].map(STATUS_LABELS).fillna(
        data["status"].str.capitalize()
    )

    for column in (
        "tarefa",
        "cliente",
        "equipamento",
        "observacao",
        "tecnico",
        "responsavel",
    ):
        data[column] = data[column].astype("string").str.strip()
        data[column] = data[column].replace("", pd.NA)

    data["data_conclusao"] = pd.to_datetime(
        data["data_conclusao"], errors="coerce"
    )
    data["data_entrega"] = pd.to_datetime(data["data_entrega"], errors="coerce")
    data["dias_atraso"] = pd.to_numeric(data["dias_atraso"], errors="coerce")
    return data


def render_dashboard(data: pd.DataFrame) -> None:
    st.caption(
        "Acompanhamento de relatórios de qualificação sincronizados com o OneDrive."
    )

    valid_dates = data["data_conclusao"].dropna()
    with st.sidebar:
        st.header("Filtros")

        selected_statuses = st.multiselect(
            "Status",
            options=sorted(data["status"].dropna().unique().tolist()),
            default=sorted(data["status"].dropna().unique().tolist()),
        )
        clients = sorted(data["cliente"].dropna().unique().tolist())
        selected_clients = st.multiselect(
            "Cliente",
            options=clients,
            default=clients,
        )
        technicians = sorted(data["tecnico"].dropna().unique().tolist())
        selected_technicians = st.multiselect(
            "Técnico",
            options=technicians,
            default=technicians,
        )

        date_range: tuple[date, date] | None = None
        if not valid_dates.empty:
            min_date = valid_dates.min().date()
            max_date = valid_dates.max().date()
            selected_dates = st.date_input(
                "Data de conclusão",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                format="DD/MM/YYYY",
            )
            if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
                date_range = (selected_dates[0], selected_dates[1])

    filtered = data[
        data["status"].isin(selected_statuses)
        & data["cliente"].isin(selected_clients)
        & data["tecnico"].isin(selected_technicians)
    ].copy()
    if date_range:
        start_date, end_date = date_range
        completion_dates = filtered["data_conclusao"].dt.date
        filtered = filtered[
            completion_dates.ge(start_date) & completion_dates.le(end_date)
        ]

    if filtered.empty:
        st.info("Nenhum relatório corresponde aos filtros selecionados.")
        return

    delivered = int(filtered["status"].eq("Entregue").sum())
    overdue = int(filtered["status"].eq("Em atraso").sum())
    cancelled = int(filtered["status"].eq("Cancelado").sum())
    delivery_days = (
        filtered.loc[
            filtered["status"].eq("Entregue")
            & filtered["data_entrega"].notna()
            & filtered["data_conclusao"].notna(),
            "data_entrega",
        ]
        - filtered.loc[
            filtered["status"].eq("Entregue")
            & filtered["data_entrega"].notna()
            & filtered["data_conclusao"].notna(),
            "data_conclusao",
        ]
    ).dt.days
    delivery_days = delivery_days[delivery_days.ge(0)]

    active_reports = len(filtered) - cancelled
    delivery_rate = delivered / active_reports * 100 if active_reports else 0
    metrics = st.columns(6)
    metrics[0].metric("Relatórios", f"{len(filtered):,}".replace(",", "."))
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
            help=f"Calculada com {len(delivery_days)} relatórios entregues com datas válidas.",
        )

    st.divider()
    status_column, monthly_column = st.columns(2)
    with status_column:
        st.subheader("Relatórios por status")
        status_counts = filtered["status"].value_counts().rename("Relatórios")
        st.bar_chart(status_counts.to_frame())

    with monthly_column:
        st.subheader("Conclusões por mês")
        monthly = filtered.dropna(subset=["data_conclusao"]).copy()
        if monthly.empty:
            st.info("Não há datas de conclusão para exibir.")
        else:
            monthly["Mês"] = monthly["data_conclusao"].dt.to_period("M").dt.to_timestamp()
            monthly_counts = (
                monthly.groupby("Mês").size().rename("Relatórios concluídos")
            )
            st.line_chart(monthly_counts.to_frame())

    client_column, technician_column = st.columns(2)
    with client_column:
        st.subheader("Clientes com mais relatórios")
        top_clients = (
            filtered["cliente"]
            .dropna()
            .value_counts()
            .head(10)
            .rename("Relatórios")
        )
        if top_clients.empty:
            st.info("Não há clientes para exibir.")
        else:
            st.bar_chart(top_clients.to_frame())

    with technician_column:
        st.subheader("Relatórios por técnico")
        technician_counts = (
            filtered["tecnico"]
            .dropna()
            .value_counts()
            .rename("Relatórios")
        )
        if technician_counts.empty:
            st.info("Não há técnicos para exibir.")
        else:
            st.bar_chart(technician_counts.to_frame())

    overdue_reports = filtered[filtered["status"].eq("Em atraso")].copy()
    if not overdue_reports.empty:
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
        st.dataframe(
            overdue_reports[
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
            ),
            width="stretch",
            hide_index=True,
        )

    with st.expander("Ver relatórios filtrados"):
        table = filtered[
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
        st.download_button(
            "Baixar dados filtrados (CSV)",
            data=table.to_csv(index=False).encode("utf-8-sig"),
            file_name="relatorios_filtrados.csv",
            mime="text/csv",
        )
        st.dataframe(table, width="stretch", hide_index=True)


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
