import os
import csv
import streamlit as st
import pandas as pd

def get_latest_file(folder_path):
    """
    Retorna o caminho do último arquivo CSV na pasta que termina com _ranked_results.csv.
    """
    files = [f for f in os.listdir(folder_path) if f.endswith("_ranked_results.csv")]
    if not files:
        return None

    def extract_datetime_from_filename(filename):
        base_name = filename.replace("_ranked_results.csv", "")
        try:
            date_part, time_part = base_name.split("_")
            return (int(date_part), int(time_part))
        except ValueError:
            return (0, 0)

    files.sort(key=extract_datetime_from_filename, reverse=True)
    return os.path.join(folder_path, files[0])

def process_week(folder_name, min_engagement=500, weights=None):
    """
    Processa os dados do último CSV encontrado na pasta informada,
    aplicando o filtro mínimo de engajamento e calculando os pesos e porcentagens.
    """
    latest_file = get_latest_file(folder_name)
    if not latest_file:
        return {}, {}

    user_max_engagement = {}

    with open(latest_file, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        # As colunas esperadas no CSV são:
        # Comments,Retweets,Likes,Bookmarks,Views,Link,User,Engagement_Total
        usuario_coluna = 'User'
        engagement_coluna = 'Engagement_Total'

        for row in reader:
            usuario = row.get(usuario_coluna, "").strip()
            
            # Obter e validar o engajamento total
            try:
                engagement = int(row.get(engagement_coluna, 0))
            except (ValueError, KeyError):
                engagement = 0

            # Aplicar o filtro mínimo de engajamento
            if engagement < min_engagement:
                continue

            # Guarda o maior engajamento encontrado para cada usuário
            if usuario not in user_max_engagement or engagement > user_max_engagement[usuario]:
                user_max_engagement[usuario] = engagement

    if not user_max_engagement:
        return {}, {}

    # Ordena os usuários pelo engajamento (maior para o menor)
    sorted_users = sorted(user_max_engagement.items(), key=lambda x: x[1], reverse=True)

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
    for idx, (usuario, engagement) in enumerate(sorted_users, start=1):
        weight = get_weight(idx, weights)
        if weight == 0:
            continue
        user_weights[usuario] = weight

    total_weights = sum(user_weights.values())
    if total_weights == 0:
        return {}, {}

    # Calcula a porcentagem do peso de cada usuário
    user_percentages = {user: (weight / total_weights) * 100 for user, weight in user_weights.items()}
    ranking_users = {usuario: idx for idx, (usuario, _) in enumerate(sorted_users, start=1) if usuario in user_weights}

    return ranking_users, user_percentages

# --- STREAMLIT APP ---
st.set_page_config(page_title="Distribuição de Recompensas", layout="wide")
st.title("Distribuição de Recompensas STREAMFLOW")

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

   **Exemplo:**
   - 1º Lugar: (18 / 135) × 100 ≈ 14,81%
   - 2º Lugar: (14 / 135) × 100 ≈ 11,11%
   - 3º Lugar: (12 / 135) × 100 ≈ 8,89%
   - ... e assim por diante.

3. **Adaptação ao Número de Participantes:**
   - A metodologia ajusta automaticamente os pesos e porcentagens conforme o número de participantes (até 30).
""")

# Neste exemplo, vamos processar as semanas 3 e 4 (pasta "csv_week3" e "csv_week4")
weeks_folders = ["csv_week3", "csv_week4"]
weeks_names = ["week3", "week4"]

st.sidebar.title("Configurações de Distribuição")

# Configuração do filtro de engajamento mínimo
min_engagement = st.sidebar.number_input(
    "Mínimo de Engagement_Total para considerar:",
    min_value=0,
    value=500,
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
    "Valor total (em dólares) a ser distribuído por semana:",
    min_value=0.0,
    value=100.0,
    step=10.0,
    format="%.2f"
)

weeks_data = {}
user_percentages_all_weeks = {}

for folder in weeks_folders:
    ranking_users, user_percentages = process_week(folder, min_engagement=min_engagement, weights=pesos_definidos)
    if ranking_users:
        weeks_data[folder] = ranking_users
        user_percentages_all_weeks[folder] = user_percentages

st.subheader("Resumo das Semanas")
col1, col2 = st.columns(2)
with col1:
    st.markdown("### Participantes por Semana")
    for folder, data in weeks_data.items():
        st.write(f"**{folder.upper()}**: {len(data)} participantes")
with col2:
    st.markdown("### Soma Total dos Pesos por Semana")
    for folder in weeks_data.keys():
        st.write(f"**{folder.upper()}**: {total_pesos} pesos")

# Inicializa os ganhos dos usuários para week3 e week4
user_earnings = {}

# Considera todos os usuários que apareceram nos CSVs processados
for folder in weeks_data:
    for user in weeks_data[folder].keys():
        if user not in user_earnings:
            user_earnings[user] = {week: 0.0 for week in weeks_names}

if weeks_data:
    st.subheader("Distribuição dos Valores por Semana")

    for folder in weeks_folders:
        if folder not in weeks_data:
            continue
        week_name = weeks_names[weeks_folders.index(folder)]
        data = weeks_data[folder]
        percentages = user_percentages_all_weeks[folder]

        st.write(f"### **{folder.upper()}**")

        week_total_valor = total_valor

        for user, rank in sorted(data.items(), key=lambda x: x[1]):
            percentage = percentages.get(user, 0)
            ganho = (percentage / 100) * week_total_valor
            user_earnings[user][week_name] += ganho
            st.write(f"- **{user}** (Rank {rank}): {ganho:.2f} USD ({percentage:.2f}%)")

    st.subheader("Ranking dos Usuários que Mais Ganharam")
    ranking_data = []
    for user, earnings in user_earnings.items():
        total = sum(earnings.values())
        ranking_data.append({
            "Usuário": user,
            "week3": earnings["week3"],
            "week4": earnings["week4"],
            "Valor Total (USD)": total
        })

    ranking_df = pd.DataFrame(ranking_data).sort_values(by="Valor Total (USD)", ascending=False).reset_index(drop=True)
    ranking_df.index += 1

    st.dataframe(ranking_df.style.format({
        "week3": "{:.2f}",
        "week4": "{:.2f}",
        "Valor Total (USD)": "{:.2f}"
    }), use_container_width=True)
else:
    st.sidebar.warning("Nenhum dado encontrado para as pastas fornecidas ou nenhum usuário atende aos critérios.")
