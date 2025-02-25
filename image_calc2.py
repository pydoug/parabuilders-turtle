import os
import csv
import streamlit as st
import pandas as pd

def get_csv_files(folder_path="."):
    """
    Retorna uma lista de arquivos CSV no diretório especificado.
    Busca especificamente o arquivo 20250225_104457_ranked_results.csv
    """
    # Caminho específico para o arquivo mencionado no GitHub
    specific_file = "20250225_104457_ranked_results.csv"
    specific_path = os.path.join(folder_path, specific_file)
    
    # Verifique se este arquivo específico existe
    if os.path.exists(specific_path):
        st.success(f"Arquivo específico encontrado: {specific_file}")
        return [specific_path]
    
    # Se não encontrar o arquivo específico, tenta buscar outros CSVs
    if not os.path.exists(folder_path):
        st.error(f"Pasta não encontrada: {folder_path}")
        return []
    
    # Busca por arquivos CSV em geral, com preferência para _ranked_results.csv
    csv_files = [f for f in os.listdir(folder_path) if f.endswith(".csv")]
    st.info(f"Arquivos CSV encontrados na pasta: {csv_files}")
    
    # Primeiro tenta encontrar arquivos ranked_results
    ranked_files = [f for f in csv_files if f.endswith("_ranked_results.csv")]
    
    # Se não encontrar, usa arquivos _export.csv
    if not ranked_files:
        export_files = [f for f in csv_files if f.endswith("_export.csv")]
        if export_files:
            # Ordena por data/hora no nome, assumindo formato YYYYMMDDTHHMM
            export_files.sort(reverse=True)
            return [os.path.join(folder_path, export_files[0])]
    
    # Se encontrou arquivos ranked_results, ordena e retorna o mais recente
    if ranked_files:
        ranked_files.sort(reverse=True)
        return [os.path.join(folder_path, ranked_files[0])]
    
    return []

def process_week(folder_name=".", min_engagement=500, weights=None, csv_file=None):
    """
    Processa os dados do CSV especificado ou do último CSV encontrado na pasta.
    
    Para cada usuário, se houver mais de um post:
    - Considera apenas o post com maior valor de Engagement_Total.
    - Agrupa a URL (coluna Link) do post selecionado.
    
    Retorna três dicionários:
      - ranking_users: mapeia o usuário para a posição (ranking) considerando os que receberam peso.
      - user_percentages: mapeia o usuário para a porcentagem correspondente.
      - aggregated_links: mapeia o usuário para a string com a URL.
    """
    if csv_file:
        file_path = csv_file
    else:
        csv_files = get_csv_files(folder_name)
        if not csv_files:
            st.error(f"Nenhum arquivo CSV encontrado em {folder_name}")
            return {}, {}, {}
        file_path = csv_files[0]
    
    # Informar qual arquivo está sendo processado
    st.info(f"Processando arquivo: {os.path.basename(file_path)}")
    
    # Dicionário para acumular dados de cada usuário
    # Estrutura: { user_lower: {"nome_original": nome, "engagement": valor, "links": [lista de urls]} }
    user_data = {}
    
    try:
        # Tentar ler o arquivo como DataFrame com pandas primeiro
        df = pd.read_csv(file_path, encoding='utf-8')
        
        # Verificar as colunas disponíveis
        columns = list(df.columns)
        st.write("Colunas disponíveis:", columns)
        
        # Identificar colunas de usuário e engajamento
        user_col = next((col for col in columns if col.lower() in ['user', 'usuario', 'usuário']), None)
        engagement_col = next((col for col in columns if col.lower() in ['engagement_total', 'engagement']), None)
        link_col = next((col for col in columns if col.lower() in ['link', 'url']), None)
        
        if not all([user_col, engagement_col, link_col]):
            st.error(f"Colunas necessárias não encontradas. Encontradas: {columns}")
            return {}, {}, {}
        
        # Processar cada linha do DataFrame
        for _, row in df.iterrows():
            user = str(row[user_col]).strip()
            user_lower = user.lower()  # Normalizar para comparação case-insensitive
            
            try:
                engagement = int(row[engagement_col])
            except (ValueError, TypeError):
                engagement = 0
            
            # Filtra pelo engajamento mínimo
            if engagement < min_engagement:
                continue
            
            link = str(row[link_col]).strip()
            
            # Se o usuário já existir, guarda apenas o post com maior engajamento
            if user_lower in user_data:
                if engagement > user_data[user_lower]["engagement"]:
                    user_data[user_lower]["engagement"] = engagement
                    user_data[user_lower]["links"] = [link] if link else []
                    # Mantém o nome original com a capitalização original
                    user_data[user_lower]["nome_original"] = user
            else:
                user_data[user_lower] = {
                    "nome_original": user,
                    "engagement": engagement, 
                    "links": [link] if link else []
                }
                
    except Exception as e:
        st.error(f"Erro ao processar o arquivo CSV: {str(e)}")
        # Tentar com o método original usando csv.DictReader
        try:
            with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                columns = reader.fieldnames
                
                # Identificar colunas
                user_col = next((col for col in columns if col.lower() in ['user', 'usuario', 'usuário']), None)
                engagement_col = next((col for col in columns if col.lower() in ['engagement_total', 'engagement']), None)
                link_col = next((col for col in columns if col.lower() in ['link', 'url']), None)
                
                if not all([user_col, engagement_col, link_col]):
                    st.error(f"Colunas necessárias não encontradas. Encontradas: {columns}")
                    return {}, {}, {}
                
                for row in reader:
                    user = row.get(user_col, "").strip()
                    user_lower = user.lower()  # Normalizar para comparação case-insensitive
                    
                    try:
                        engagement = int(row.get(engagement_col, 0))
                    except (ValueError, KeyError):
                        engagement = 0
                    
                    # Filtra pelo engajamento mínimo
                    if engagement < min_engagement:
                        continue
                    
                    link = row.get(link_col, "").strip()
                    
                    # Se o usuário já existir, guarda apenas o post com maior engajamento
                    if user_lower in user_data:
                        if engagement > user_data[user_lower]["engagement"]:
                            user_data[user_lower]["engagement"] = engagement
                            user_data[user_lower]["links"] = [link] if link else []
                            # Mantém o nome original com a capitalização original
                            user_data[user_lower]["nome_original"] = user
                    else:
                        user_data[user_lower] = {
                            "nome_original": user,
                            "engagement": engagement, 
                            "links": [link] if link else []
                        }
        except Exception as e2:
            st.error(f"Falha no método alternativo também: {str(e2)}")
            return {}, {}, {}
    
    if not user_data:
        st.warning("Nenhum dado encontrado que atenda aos critérios de engajamento mínimo.")
        return {}, {}, {}
    
    # Exibir usuários encontrados
    st.write(f"Foram encontrados {len(user_data)} usuários com engajamento acima de {min_engagement}:")
    for user_lower, data in user_data.items():
        st.write(f"- {data['nome_original']} (Engajamento: {data['engagement']})")
    
    # Ordena os usuários por engajamento (maior para o menor)
    sorted_users = sorted(user_data.items(), key=lambda x: x[1]["engagement"], reverse=True)
    
    def get_weight(position, weights_dict):
        if position in weights_dict:
            return weights_dict[position]
        elif 6 <= position <= 15:
            return weights_dict.get('6-15', 4)
        elif 16 <= position <= 30:
            return weights_dict.get('16-30', 2)
        else:
            return 0
    
    user_weights = {}
    aggregated_links = {}
    for idx, (user_lower, data) in enumerate(sorted_users, start=1):
        weight = get_weight(idx, weights)
        if weight == 0:
            continue
        
        # Usar o nome original (preservando capitalização)
        original_name = data["nome_original"]
        user_weights[original_name] = weight
        
        # Agrupa as URLs separando por espaço (neste caso, será apenas uma URL)
        aggregated_links[original_name] = " ".join(data["links"])
    
    total_weights = sum(user_weights.values())
    if total_weights == 0:
        st.warning("Nenhum usuário recebeu peso. Verifique suas configurações de pesos.")
        return {}, {}, {}
    
    user_percentages = {user: (weight / total_weights) * 100 for user, weight in user_weights.items()}
    
    # Ranking dos usuários mantendo o nome original
    ranking_users = {}
    for idx, (user_lower, data) in enumerate(sorted_users, start=1):
        original_name = data["nome_original"]
        if original_name in user_weights:
            ranking_users[original_name] = idx
    
    return ranking_users, user_percentages, aggregated_links

# --- STREAMLIT APP ---
st.set_page_config(page_title="Distribuição de Recompensas", layout="wide")
st.title("Distribuição de Recompensas TURTLE")

st.markdown("""
## **Metodologia para Distribuição Dinâmica de Prêmios**

1. **Pesos por Posição:** Cada posição recebe um peso que determina a porcentagem do prêmio total. Pesos decrescem conforme a posição.

   **Exemplo de Pesos:**
   - 1º Lugar: 18
   - 2º Lugar: 14
   - 3º Lugar: 12
   - 4º Lugar: 10
   - 5º Lugar: 9
   - 6º a 15º Lugar: 7 cada
   - 16º a 30º Lugar: 5 cada

2. **Cálculo das Porcentagens:**
   - **Fórmula:**
     Porcentagem da Posição = (Peso da Posição / Soma Total dos Pesos) × 100%

3. **Agregação de Posts:**
   - Para cada usuário, é considerado apenas o post com maior Engagement_Total, e a URL desse post é utilizada.
""")

st.sidebar.title("Configurações de Distribuição")

# Seletor de arquivo CSV (opcional)
uploaded_file = st.sidebar.file_uploader("Carregar CSV (opcional)", type=["csv"])
use_uploaded = st.sidebar.checkbox("Usar arquivo carregado", value=False)

if uploaded_file and use_uploaded:
    st.sidebar.success("Arquivo carregado com sucesso!")
    # Salvar arquivo temporariamente
    with open("temp_upload.csv", "wb") as f:
        f.write(uploaded_file.getbuffer())
    csv_file = "temp_upload.csv"
else:
    csv_file = None

# Filtro de engajamento mínimo
min_engagement = st.sidebar.number_input(
    "Mínimo de Engagement_Total para considerar:",
    min_value=0,
    value=400,
    step=100
)

# Inputs para os pesos
peso_1 = st.sidebar.number_input("Peso para 1º Lugar:", min_value=0, max_value=100, value=18, step=1)
peso_2 = st.sidebar.number_input("Peso para 2º Lugar:", min_value=0, max_value=100, value=14, step=1)
peso_3 = st.sidebar.number_input("Peso para 3º Lugar:", min_value=0, max_value=100, value=12, step=1)
peso_4 = st.sidebar.number_input("Peso para 4º Lugar:", min_value=0, max_value=100, value=10, step=1)
peso_5 = st.sidebar.number_input("Peso para 5º Lugar:", min_value=0, max_value=100, value=9, step=1)
peso_6_15 = st.sidebar.number_input("Peso para 6º a 15º Lugar:", min_value=0, max_value=100, value=7, step=1)
peso_16_30 = st.sidebar.number_input("Peso para 16º a 30º Lugar:", min_value=0, max_value=100, value=5, step=1)

pesos_definidos = {
    1: peso_1,
    2: peso_2,
    3: peso_3,
    4: peso_4,
    5: peso_5,
    '6-15': peso_6_15,
    '16-30': peso_16_30
}

total_pesos = peso_1 + peso_2 + peso_3 + peso_4 + peso_5 + (peso_6_15 * 10) + (peso_16_30 * 15)

st.sidebar.markdown("### Pesos Definidos")
st.sidebar.write(f"**1º Lugar:** {peso_1}")
st.sidebar.write(f"**2º Lugar:** {peso_2}")
st.sidebar.write(f"**3º Lugar:** {peso_3}")
st.sidebar.write(f"**4º Lugar:** {peso_4}")
st.sidebar.write(f"**5º Lugar:** {peso_5}")
st.sidebar.write(f"**6º a 15º Lugar:** {peso_6_15} cada")
st.sidebar.write(f"**16º a 30º Lugar:** {peso_16_30} cada")
st.sidebar.markdown(f"**Soma Total dos Pesos:** {total_pesos}")

total_valor = st.sidebar.number_input(
    "Valor total (em dólares) a ser distribuído:",
    min_value=0.0,
    value=150.0,
    step=10.0,
    format="%.2f"
)

# Seleção de pasta - definindo csv_week2 como padrão
folder_options = ["csv_week2", "."]
folder = st.sidebar.selectbox("Selecione a pasta para buscar o CSV:", folder_options, index=0)

# Aviso sobre o arquivo específico
st.sidebar.info("Configurado para buscar preferencialmente o arquivo: 20250225_104457_ranked_results.csv")

# Processar dados
ranking_users, user_percentages, aggregated_links = process_week(
    folder_name=folder, 
    min_engagement=min_engagement, 
    weights=pesos_definidos, 
    csv_file=csv_file if use_uploaded and uploaded_file else None
)

if ranking_users:
    st.subheader("Resumo da Distribuição")
    st.write(f"**Total de participantes:** {len(ranking_users)}")
    st.write(f"**Soma Total dos Pesos:** {total_pesos}")
    
    st.subheader("Distribuição dos Valores")
    user_earnings = {}
    user_links = {}

    week_name = "week1"  # Nome definido para a única semana em análise
    week_total_valor = total_valor

    for user, rank in sorted(ranking_users.items(), key=lambda x: x[1]):
        percentage = user_percentages.get(user, 0)
        ganho = (percentage / 100) * week_total_valor

        user_earnings[user] = {week_name: ganho}
        user_links[user] = aggregated_links.get(user, "")

        st.write(f"- **{user}** (Rank {rank}): {ganho:.2f} USD ({percentage:.2f}%) | Links: {aggregated_links.get(user, '')}")

    st.subheader("Ranking dos Usuários que Mais Ganharam")
    ranking_data = []
    for user, earnings in user_earnings.items():
        total = earnings[week_name]
        ranking_data.append({
            "Usuário": user,
            week_name: earnings[week_name],
            "Valor Total (USD)": total,
            "Links": user_links.get(user, "")
        })

    ranking_df = pd.DataFrame(ranking_data).sort_values(by="Valor Total (USD)", ascending=False).reset_index(drop=True)
    ranking_df.index += 1

    st.dataframe(ranking_df.style.format({
        week_name: "{:.2f}",
        "Valor Total (USD)": "{:.2f}"
    }), use_container_width=True)
    
    # Opção para download
    csv_download = ranking_df.to_csv(index=True).encode('utf-8')
    st.download_button(
        label="Download CSV do resultado",
        data=csv_download,
        file_name=f"resultado_distribuicao_{min_engagement}.csv",
        mime="text/csv",
    )
else:
    st.warning("Nenhum dado encontrado que atenda aos critérios selecionados. Por favor, verifique as configurações ou o arquivo CSV.")
