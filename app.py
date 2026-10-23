import streamlit as st
import msal
import requests
import pandas as pd
import io

# Credenciais armazenadas em st.secrets
CLIENT_ID = st.secrets["microsoft"]["client_id"]
TENANT_ID = st.secrets["microsoft"]["tenant_id"]
CLIENT_SECRET = st.secrets["microsoft"]["client_secret"]

# 2. Configurações do arquivo e do usuário
# Como estamos usando permissão de aplicativo, a Graph API precisa saber DE QUAL usuário baixar
USER_EMAIL = "metrologia03@rstechengenharia.onmicrosoft.com"
FILE_NAME = "Controle de Relatórios.xlsx"

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["https://graph.microsoft.com/.default"]

# O cache evita que a API seja chamada toda vez que você clica em algo na tela (TTL = 1 hora)
@st.cache_data(ttl=3600)
def load_data_from_onedrive():
    # 3. Autenticação invisível com MSAL
    app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET
    )
    
    token_response = app.acquire_token_for_client(scopes=SCOPE)
    
    if "access_token" not in token_response:
        st.error("Erro de autenticação com o Azure. Verifique as chaves.")
        return None
        
    access_token = token_response["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 4. Requisição de download na Graph API
    # O comando :/content traz o arquivo físico, não apenas os metadados
    url = f"https://graph.microsoft.com/v1.0/users/{USER_EMAIL}/drive/root:/{FILE_NAME}:/content"
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        # 5. Converte os bytes recebidos em um DataFrame Pandas sem gravar no disco
        excel_data = io.BytesIO(response.content)
        df = pd.read_excel(excel_data)
        return df
    else:
        st.error(f"Erro ao acessar planilha: Erro {response.status_code}")
        st.write(response.json())
        return None

# Interface do Streamlit
st.title("Dashboard: Controle de Relatórios")

df_relatorios = load_data_from_onedrive()

if df_relatorios is not None:
    st.success("Planilha sincronizada com sucesso!")
    
    # Exibe as primeiras 5 linhas para validar se a leitura funcionou
    st.dataframe(df_relatorios.head())