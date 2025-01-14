import streamlit as st
import pandas as pd
import json

# Configurar o Streamlit para Wide Mode
st.set_page_config(layout="wide", page_title="Análise Kaisar")

# Caminho do arquivo JSON
file_path = 'dados/formulario.json'

# Carregar os dados do arquivo JSON
with open(file_path, 'r', encoding='utf-8') as file:
    data = json.load(file)

# Converter os dados para um DataFrame
df = pd.DataFrame(data)

# Converter coluna "Seguidores no Twitter" para numérico
df['Seguidores no Twitter'] = pd.to_numeric(df['Seguidores no Twitter'], errors='coerce')

# Calcular a quantidade total de seguidores no Twitter
total_followers = df['Seguidores no Twitter'].sum()

# Número total de inscritos (número de linhas no DataFrame)
total_subscribers = len(df)

# Exibir o título do aplicativo
st.title("Análise de Criadores da Kaisar")

# Mostrar os dados na interface
st.subheader("Dados dos Criadores")
st.dataframe(df)

# Exibir o número de inscritos e total de seguidores
st.subheader("Estatísticas")

# Exibir os valores diretamente
st.write(f"**Número Total de Inscritos:** {total_subscribers}")
st.write(f"**Total de Seguidores no Twitter:** {total_followers}")

# Permitir download dos dados como CSV
st.subheader("Baixar os Dados")
csv = df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Baixar CSV",
    data=csv,
    file_name='criadores_kaisar.csv',
    mime='text/csv'
)
