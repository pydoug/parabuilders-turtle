import os
import csv
import streamlit as st
import pandas as pd

def get_latest_file(folder_path):
    """
    Retorna o caminho do último arquivo CSV na pasta que termina com _ranked_results.csv.
    """
    if not os.path.exists(folder_path):
        return None
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
    Processa os dados do último CSV encontrado na pasta informada.
    
    Para cada usuário, se houver mais de um post:
    - Soma os valores de Engagement_Total.
    - Agrupa as URLs (coluna Link) em uma única string (separadas por espaço).

    Retorna três dicionários:
      - ranking_users: mapeia o usuário para a posição (ranking) considerando os que receberam peso.
      - user_percentages: mapeia o usuário para a porcentagem correspondente.
      - aggregated_links: mapeia o usuário para a string com as URLs agregadas.
    """
    latest_file = get_latest_file(folder_name)
    if not latest_file:
        return {}, {}, {}

    # Dicionário para acumular dados de cada usuário
    # Estrutura: { user: {"engagement": valor_total, "links": [lista de urls]} }
    user_data = {}

    with open(latest_file, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        # As colunas esperadas: Comments,Retweets,Likes,Bookmarks,Views,Link,User,Engagement_Total
        usuario_coluna = 'User'
        engagement_coluna = 'Engagement_Total'
        link_coluna = 'Link'

        for row in reader:
            user = row.get(usuario_coluna, "").strip()
            try:
                engagement = int(row.get(engagement_coluna, 0))
            except (ValueError, KeyError):
                engagement = 0

            # Filtra pelo engajamento mínimo
            if engagement < min_engagement:
                continue

            link = row.get(link_coluna, "").strip()
            if user in user_data:
                user_data[user]["engagement"] += engagement
                if link:
                    user_data[user]["links"].append(link)
            else:
                user_data[user] = {"engagement": engagement, "links": []}
                if link:
                    user_data[user]["links"].append(link)

    if not user_data:
        return {}, {}, {}

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
    for idx, (user, data) in enumerate(sorted_users, start=1):
        weight = get_weight(idx, weights)
        if weight == 0:
            continue
        user_weights[user] = weight
        # Agrupa as URLs separando por espaço
        aggregated_links[user] = " ".join(data["links"])

    total_weights = sum(user_weights.values())
    if total_weights == 0:
        return {}, {}, {}

    user_percentages = {user: (weight / total_weights) * 100 for user, weight in user_weights.items()}
    ranking_users = {user: idx for idx, (user, _) in enumerate(sorted_users, start=1) if user in user_weights}

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
   - Se um usuário tiver mais de um post, o valor de Engagement_Total é somado e as URLs (coluna Link) são concatenadas, separadas por um espaço.
""")

# Usaremos as pastas para as semanas 1 e 2
weeks_folders = ["csv_week1", "csv_week2"]
weeks_names = ["week1", "week2"]

st.sidebar.title("Configurações de Distribuição")

# Filtro de engajamento mínimo
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

# Processa cada semana e armazena os resultados
weeks_data = {}
user_percentages_all_weeks = {}
links_all_weeks = {}

for folder in weeks_folders:
    ranking_users, user_percentages, aggregated_links = process_week(folder, min_engagement=min_engagement, weights=pesos_definidos)
    if ranking_users:
        weeks_data[folder] = ranking_users
        user_percentages_all_weeks[folder] = user_percentages
        links_all_weeks[folder] = aggregated_links

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

# Inicializa os ganhos e as URLs dos usuários para week1 e week2
user_earnings = {}
user_links = {}

if weeks_data:
    st.subheader("Distribuição dos Valores por Semana")

    for folder in weeks_folders:
        if folder not in weeks_data:
            continue
        week_name = weeks_names[weeks_folders.index(folder)]
        data = weeks_data[folder]
        percentages = user_percentages_all_weeks[folder]
        week_links = links_all_weeks[folder]

        st.write(f"### **{folder.upper()}**")
        week_total_valor = total_valor

        for user, rank in sorted(data.items(), key=lambda x: x[1]):
            percentage = percentages.get(user, 0)
            ganho = (percentage / 100) * week_total_valor

            if user not in user_earnings:
                user_earnings[user] = {week: 0.0 for week in weeks_names}
            user_earnings[user][week_name] += ganho

            # Agrupa as URLs de cada semana para o usuário
            if user not in user_links:
                user_links[user] = ""
            # Se já houver links, adiciona um espaço antes de concatenar
            if week_links.get(user):
                if user_links[user]:
                    user_links[user] += " "
                user_links[user] += week_links[user]

            st.write(f"- **{user}** (Rank {rank}): {ganho:.2f} USD ({percentage:.2f}%) | Links: {week_links.get(user, '')}")

    st.subheader("Ranking dos Usuários que Mais Ganharam")
    ranking_data = []
    for user, earnings in user_earnings.items():
        total = sum(earnings.values())
        ranking_data.append({
            "Usuário": user,
            "week1": earnings["week1"],
            "week2": earnings["week2"],
            "Valor Total (USD)": total,
            "Links": user_links.get(user, "")
        })

    ranking_df = pd.DataFrame(ranking_data).sort_values(by="Valor Total (USD)", ascending=False).reset_index(drop=True)
    ranking_df.index += 1

    st.dataframe(ranking_df.style.format({
        "week1": "{:.2f}",
        "week2": "{:.2f}",
        "Valor Total (USD)": "{:.2f}"
    }), use_container_width=True)
else:
    st.sidebar.warning("Nenhum dado encontrado para as pastas fornecidas ou nenhum usuário atende aos critérios.")
