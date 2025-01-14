import streamlit as st
import requests
import base64
import json

def main():
    st.title("Formulário de Cadastro - Campanha Turtle")

    # Apresentação
    st.markdown(
        """
        A Turtle é um protocolo de distribuição Web3 que ajuda a monetizar as atividades dos usuários, trazendo recompensas de fora para dentro. Em outras palavras, a Turtle quer facilitar a obtenção de recompensas enquanto você farma algum airdrop. 🐢  

        Uma analogia simples para entender a Turtle é imaginar um programa de fidelidade de um supermercado. Normalmente, você acumula pontos comprando produtos e depois troca esses pontos por recompensas. Da mesma forma, a Turtle transforma suas interações e atividades em recompensas reais! 💎

        ### **Detalhes da Campanha**
        - **Início:** 15/01 às 20h
        - **Encerramento:** 22/01 às 22h
        - **Premiação Total:** $150

        Participe e aproveite essa oportunidade de fazer parte da revolução Turtle! 🌟
        """
    )

    # Perguntas do formulário
    st.header("Informações de Cadastro")

    # Twitter
    twitter_handle = st.text_input("Twitter:", placeholder="Ex: @dollarinveste")
    twitter_followers = st.text_input("Quantos seguidores você tem no Twitter?", placeholder="Digite o número de seguidores")

    # Discord
    discord_handle = st.text_input("Discord:", placeholder="Ex: @dollarinveste")
    is_turtle_member = st.radio(
        "Já participa do Discord da Turtle?",
        options=["Sim", "Não"],
    )

    creator_role = None
    if is_turtle_member == "Sim":
        creator_role = st.radio(
            "Você já possui cargo de creator na Turtle?",
            options=["Sim, Creator Oficial", "Ainda não"],
        )

    # Consentimento para compartilhar informações
    consent = st.radio(
        "Você concorda em compartilhar essas informações conosco?",
        options=["Sim", "Não"],
    )

    # Botão de Envio
    if st.button("Enviar"):
        if consent == "Sim":
            data = {
                "Twitter": twitter_handle,
                "Seguidores no Twitter": twitter_followers,
                "Discord": discord_handle,
                "Participa do Discord da Turtle": is_turtle_member,
                "Cargo na Turtle": creator_role if is_turtle_member == "Sim" else "N/A",
            }
            upload_to_github(data)
            st.success("Obrigado por enviar suas informações! Entraremos em contato em breve.")
        else:
            st.warning("Você precisa concordar em compartilhar as informações para enviar o formulário.")

def upload_to_github(data):
    # Configurações do GitHub
    repo = "pydoug/parabuilders-turtle"
    token = "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"
    path = "dados/formulario.json"

    # URL do arquivo no repositório
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {"Authorization": f"token {token}"}

    # Obter conteúdo existente
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        # Arquivo existe, atualizando
        file_info = response.json()
        sha = file_info["sha"]
        content = json.loads(base64.b64decode(file_info["content"].encode()).decode())
        content.append(data)
    elif response.status_code == 404:
        # Arquivo não existe, criando novo
        sha = None
        content = [data]
    else:
        # Erro inesperado
        st.error(f"Erro ao acessar o repositório: {response.status_code} - {response.json().get('message', 'Erro desconhecido')}")
        return

    # Preparar o payload para upload
    payload = {
        "message": "Atualização do formulário",
        "content": base64.b64encode(json.dumps(content, indent=4).encode()).decode(),
        "sha": sha,
    }

    # Enviar atualização ao GitHub
    response = requests.put(url, headers=headers, json=payload)

    if response.status_code in [200, 201]:
        st.info("Dados enviados com sucesso ao GitHub!")
    else:
        st.error(f"Erro ao enviar dados ao GitHub: {response.status_code} - {response.json().get('message', 'Erro desconhecido')}")

if __name__ == "__main__":
    main()
