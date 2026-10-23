import io

import msal
import pandas as pd
import requests
import streamlit as st


USER_EMAIL = "metrologia03@rstechengenharia.onmicrosoft.com"
FILE_PATH = "01 - DRIVE METROLOGIA/Controle de Relatórios.xlsx"
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
REPORT_COLUMNS = {
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


@st.cache_data(ttl=3600)
def load_data_from_onedrive() -> pd.DataFrame:
    microsoft_secrets = st.secrets["microsoft"]
    authority = (
        "https://login.microsoftonline.com/" + microsoft_secrets["tenant_id"]
    )
    client = msal.ConfidentialClientApplication(
        microsoft_secrets["client_id"],
        authority=authority,
        client_credential=microsoft_secrets["client_secret"],
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
        headers={"Authorization": "Bearer " + access_token},
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
    data = data.rename(columns=lambda column: str(column).strip())
    missing_columns = set(REPORT_COLUMNS).difference(data.columns)
    if missing_columns:
        raise ValueError(
            "A planilha não contém todas as colunas esperadas: "
            + ", ".join(sorted(missing_columns))
        )

    data = data.rename(columns=REPORT_COLUMNS)
    data["status"] = data["status"].astype("string").str.strip().str.upper()
    data = data[data["status"].notna() & data["status"].ne("")].copy()
    data["status"] = data["status"].map(STATUS_LABELS).fillna(
        data["status"].str.capitalize()
    )

    text_columns = (
        "tarefa",
        "cliente",
        "equipamento",
        "observacao",
        "tecnico",
        "responsavel",
    )
    for column in text_columns:
        data[column] = data[column].astype("string").str.strip()
        data[column] = data[column].replace("", pd.NA)

    data["data_conclusao"] = pd.to_datetime(
        data["data_conclusao"], errors="coerce"
    )
    data["data_entrega"] = pd.to_datetime(data["data_entrega"], errors="coerce")
    data["dias_atraso"] = pd.to_numeric(data["dias_atraso"], errors="coerce")
    return data
