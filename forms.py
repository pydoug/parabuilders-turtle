import streamlit as st
import json
import requests
import os
import base64
from dotenv import load_dotenv

# Carregar variáveis do arquivo .env
load_dotenv()

# Configurar o token do GitHub e o repositório
github_token = os.getenv("GITHUB_TOKEN")
github_repo = "pydoug/parabuilders-turtle"  # Substitua pelo seu repositório no GitHub
if not github_token:
    st.error("Token do GitHub não encontrado. Configure no arquivo .env.")
    st.stop()

# Função para salvar dados no GitHub
def salvar_no_github(file_path, data, commit_message):
    """
    Salva um arquivo JSON no repositório do GitHub.
    """
    url = f"https://api.github.com/repos/{github_repo}/contents/{file_path}"
    headers = {"Authorization": f"token {github_token}"}

    # Verificar se o arquivo já existe no GitHub
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        sha = response.json().get("sha")  # SHA do arquivo existente
    else:
        sha = None

    # Codificar os dados em base64
    content = json.dumps(data, ensure_ascii=False, indent=4).encode("utf-8")
    payload = {
        "message": commit_message,
        "content": base64.b64encode(content).decode("utf-8"),
    }
    if sha:
        payload["sha"] = sha

    # Enviar o arquivo para o GitHub
    response = requests.put(url, headers=headers, json=payload)
    if response.status_code in [200, 201]:
        st.success(f"Arquivo {file_path} salvo com sucesso no GitHub!")
    else:
        st.error(f"Erro ao salvar {file_path}: {response.json()}")

# Função principal
def main():
    st.title("Formulário de Cadastro - Campanha Turtle 🐢")

    st.markdown(
        """
        A **Turtle** é um protocolo de distribuição Web3 que ajuda a monetizar as atividades dos usuários, trazendo recompensas reais.  
        Participe e aproveite essa oportunidade de fazer parte da revolução Turtle! 🌟
        """
    )

    st.header("Informações de Cadastro")

    # Formulário
    twitter_handle = st.text_input("Twitter:", placeholder="Ex: @seuusuario")
    twitter_followers = st.text_input("Quantos seguidores você tem no Twitter?", placeholder="Digite o número")
    discord_handle = st.text_input("Discord:", placeholder="Ex: SeuUsuario#1234")
    is_turtle_member = st.radio("Já participa do Discord da Turtle?", options=["Sim", "Não"])
    creator_role = None
    if is_turtle_member == "Sim":
        creator_role = st.radio(
            "Você já possui cargo de creator na Turtle?",
            options=["Sim, Creator Oficial", "Ainda não"]
        )

    consent = st.radio(
        "Você concorda em compartilhar essas informações conosco?",
        options=["Sim", "Não"]
    )

    if st.button("Enviar"):
        if consent == "Sim":
            # Dados a serem salvos
            data = {
                "Twitter": twitter_handle,
                "Seguidores no Twitter": twitter_followers,
                "Discord": discord_handle,
                "Participa do Discord da Turtle": is_turtle_member,
                "Cargo na Turtle": creator_role if is_turtle_member == "Sim" else "N/A",
            }
            salvar_no_github("dados/formulario.json", data, "Atualização do formulário")
        else:
            st.warning("Você precisa concordar em compartilhar as informações para enviar o formulário.")

if __name__ == "__main__":
    main()
