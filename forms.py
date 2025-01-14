import openai
import streamlit as st
import os
import json
import uuid
import requests
from dotenv import load_dotenv

# Carregar variáveis do arquivo .env
load_dotenv()

# Configurar a chave da API OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    st.error("Chave da API OpenAI não encontrada. Configure no arquivo .env.")
    st.stop()

# Configurar o token do GitHub e o repositório
github_token = os.getenv("GITHUB_TOKEN")
github_repo = "seu-usuario/IA-ParaBuilders"  # Substitua pelo seu repositório
if not github_token:
    st.error("Token do GitHub não encontrado. Configure no arquivo .env.")
    st.stop()

# Gera um ID único para cada sessão
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())
    st.session_state["historico"] = []

session_id = st.session_state["session_id"]
historico_path = f"sessions/{session_id}.json"
feedback_path = f"feedbacks/{session_id}.json"

# Função para salvar arquivos JSON no GitHub
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
        "content": content.decode("utf-8"),
    }
    if sha:
        payload["sha"] = sha

    # Enviar para o GitHub
    response = requests.put(url, headers=headers, json=payload)
    if response.status_code in [200, 201]:
        st.success(f"Arquivo {file_path} salvo no GitHub.")
    else:
        st.error(f"Erro ao salvar {file_path}: {response.json()}")

# Contexto da ParaBuilders e Codorna
contexto = """
Você é uma IA da ParaBuilders, uma comunidade Web3 dedicada a criadores de conteúdo, moderadores, community managers e outros profissionais do ecossistema Web3. 
Sua personalidade reflete a cultura da ParaBuilders e das codornas:
- Engraçada e acolhedora, com toques de sarcasmo inteligente.
- Sempre focada em apoiar, ensinar e promover o lema "Codorna ajuda Codorna".
- Inspira e motiva os membros a se destacarem no mercado Web3.

Sobre a ParaBuilders:
A ParaBuilders é uma comunidade focada na profissionalização da Web3, promovendo workshops, mentorias e networking para criadores de conteúdo e outros profissionais. 
Ela conecta talentos brasileiros com grandes empresas internacionais, oferecendo treinamento gratuito e oportunidades exclusivas. 
Os membros que se destacam tornam-se "Creators Oficiais", com acesso a aulas avançadas, certificados, e cargos especiais na comunidade.

Valores:
- "Codorna ajuda Codorna": União, companheirismo e prosperidade.
- Foco no aprendizado e compartilhamento de conhecimento.
- Criar um ecossistema sustentável e de alta qualidade no mercado Web3.

Missão:
- Capacitar criadores de conteúdo e outros profissionais a conquistar seu espaço na Web3.
- Tornar o Brasil um destaque global no mercado cripto e blockchain.

Use esse contexto para responder a perguntas, corrigir textos, ensinar conceitos ou motivar a comunidade. 
Mantenha o tom engraçado, acolhedor e criativo, mas sem perder o foco nos objetivos da ParaBuilders.
"""

# Função para interagir com a IA
def interagir_com_ia(mensagem_usuario):
    """
    Envia uma mensagem para a IA com o contexto configurado.
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": contexto},
            {"role": "user", "content": mensagem_usuario},
        ]
    )

    # Retorna a resposta gerada pela IA
    return response["choices"][0]["message"]["content"].strip()


# Aplicação Streamlit
st.title("Chatbot ParaBuilders 🏗️ 🐤")
st.write("Converse com a IA da ParaBuilders e aprenda mais sobre o mundo Web3 e a cultura das codornas!")

# Caixa de entrada do usuário
mensagem_usuario = st.text_input("Digite sua mensagem aqui:")

# Quando o usuário enviar uma mensagem
if st.button("Enviar"):
    if mensagem_usuario:
        # Adicionar a mensagem do usuário ao histórico
        st.session_state["historico"].append({"role": "user", "content": mensagem_usuario})

        # Obter resposta da IA
        resposta_ia = interagir_com_ia(mensagem_usuario)

        # Adicionar a resposta da IA ao histórico
        st.session_state["historico"].append({"role": "assistant", "content": resposta_ia})

        # Salvar histórico no GitHub
        salvar_no_github(historico_path, st.session_state["historico"], "Atualizar histórico de conversa")

# Mostrar o histórico de conversas
st.write("### Conversa:")
for mensagem in st.session_state["historico"]:
    if mensagem["role"] == "user":
        st.markdown(f"**Você:** {mensagem['content']}")
    else:
        st.markdown(f"**IA:** {mensagem['content']}")

# Caixa de feedback
st.write("### Feedback:")
feedback_text = st.text_area("Deixe seu feedback aqui:")

if st.button("Enviar Feedback"):
    if feedback_text.strip():
        salvar_no_github(feedback_path, {"session_id": session_id, "feedback": feedback_text.strip()}, "Adicionar feedback")
        st.success("Obrigado pelo feedback!")
