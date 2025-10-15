import streamlit as st
import pandas as pd
import datetime
import base64
import requests
import json

st.set_page_config(page_title="Questionário de Rotina", page_icon="📝")

st.title("📝 Questionário de Rotina em Casa")
st.write("Responda às perguntas abaixo. Suas respostas serão salvas em um arquivo CSV no GitHub.")

# --- Perguntas ---
with st.form("formulario"):
    nome = st.text_input("Seu nome (opcional)")
    q1 = st.text_area("1️⃣ Quais são as maiores dificuldades que você encontra no seu dia a dia em casa?")
    q2 = st.text_area("2️⃣ O que costuma fazer quando precisa de ajuda ou quando algo dá errado (ex.: um problema de saúde ou uma emergência)?")
    q3 = st.text_area("3️⃣ O que deixaria a sua rotina mais fácil e confortável?")
    enviar = st.form_submit_button("Enviar respostas")

# --- Configurações ---
REPO = st.secrets["repo"]  # ex: "usuario/meu-repo"
FILE_PATH = "respostas.csv"
TOKEN = st.secrets["github_token"]  # Personal Access Token com permissão "repo"

# Função: obtém o conteúdo atual do CSV no GitHub
def get_csv_from_github():
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {TOKEN}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        data = r.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        sha = data["sha"]
        df = pd.read_csv(pd.io.common.StringIO(content))
        return df, sha
    elif r.status_code == 404:
        # arquivo ainda não existe
        df = pd.DataFrame(columns=["timestamp", "nome", "pergunta1", "pergunta2", "pergunta3"])
        return df, None
    else:
        st.error(f"Erro ao acessar o repositório: {r.status_code}")
        st.stop()

# Função: envia o CSV atualizado para o GitHub
def update_csv_to_github(df, sha=None):
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {TOKEN}"}
    content = df.to_csv(index=False).encode("utf-8")
    b64content = base64.b64encode(content).decode("utf-8")

    message = f"Nova resposta adicionada em {datetime.datetime.utcnow().isoformat()}"

    data = {
        "message": message,
        "content": b64content,
        "branch": "main"  # ou o nome da branch principal do seu repo
    }
    if sha:
        data["sha"] = sha

    r = requests.put(url, headers=headers, data=json.dumps(data))
    if r.status_code not in [200, 201]:
        st.error(f"Erro ao atualizar CSV: {r.status_code}, {r.text}")
        st.stop()

# Quando o usuário enviar o formulário
if enviar:
    if not (q1 or q2 or q3):
        st.warning("Preencha pelo menos uma resposta antes de enviar.")
    else:
        with st.spinner("Salvando suas respostas..."):
            df, sha = get_csv_from_github()
            nova_linha = {
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "nome": nome,
                "pergunta1": q1,
                "pergunta2": q2,
                "pergunta3": q3
            }
            df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
            update_csv_to_github(df, sha)
        st.success("✅ Resposta enviada com sucesso! Obrigado por participar.")

# --- Mostrar respostas ---
if st.checkbox("📊 Mostrar respostas já enviadas"):
    df, _ = get_csv_from_github()
    st.dataframe(df)
