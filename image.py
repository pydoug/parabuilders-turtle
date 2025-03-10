import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import time

# Set up a debug flag
DEBUG = True  # Set to False to reduce verbosity

def debug_print(*args):
    if DEBUG:
        print(*args)

# Set Streamlit page configuration
st.set_page_config(
    page_title="ParaBuilders x TURTLE Dashboard",
    page_icon=":bar_chart:",
    layout="wide"  # Define the wide layout
)

# URLs for logos
parabuilders_logo_url = "https://img001.prntscr.com/file/img001/VKycI-v6Sx6BQ1JXBqC7yA.png"  # ParaBuilders logo
turtle_logo_url = "https://via.placeholder.com/150x150.png?text=TURTLE"  # Placeholder URL for TURTLE logo

# Display header with logos and title
st.markdown(
    f"""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin-bottom: 20px;">
        <div style="display: flex; align-items: center; justify-content: center; gap: 20px; flex-wrap: wrap;">
            <img src="{parabuilders_logo_url}" alt="ParaBuilders Logo" style="height: 80px;"/>
            <img src="{turtle_logo_url}" alt="TURTLE Logo" style="height: 190px;"/>
        </div>
        <h1 style="text-align: center; font-size: 40px; margin-top: 10px;">
            Campaign ParaBuilders x TURTLE
        </h1>
    </div>
    """,
    unsafe_allow_html=True
)

# Week selection menu
selected_week = st.radio(
    "Select Week:",
    ["Week1", "Week2", "Week3", "Week4", "All Weeks"],
    horizontal=True
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Diretório base do repositório

week_directories = {
    'Week1': os.path.join(BASE_DIR, "csv_week1"),
    'Week2': os.path.join(BASE_DIR, "csv_week2"),
    'Week3': os.path.join(BASE_DIR, "csv_week3"),
    'Week4': os.path.join(BASE_DIR, "csv_week4"),
}

# Set the CSV directories based on the selected week
if selected_week == 'All Weeks':
    CSV_DIRS = [
        week_directories['Week1'],
        week_directories['Week2'],
        week_directories['Week3'],
        week_directories['Week4']
    ]
else:
    CSV_DIRS = [week_directories[selected_week]]

def extract_datetime_from_filename(filename):
    """
    Extract datetime from the filename.
    Expected format: YYYYMMDD_HHMMSS_ranked_results.csv
    """
    try:
        datetime_part = filename.split("_ranked_results")[0]  # Remove o sufixo do nome
        return pd.to_datetime(datetime_part, format="%Y%m%d_%H%M%S")
    except Exception as e:
        debug_print(f"[ERROR] Failed to extract datetime from filename '{filename}': {e}")
        return pd.NaT

def ensure_engagement_total(df):
    """
    Garante que a coluna 'Engagement_Total' exista.
    Se não existir, calcula usando a fórmula:
    Engagement_Total = Views + (Comments x 6) + (Retweets x 3) + (Likes x 2) + (Bookmarks)
    """
    if 'Engagement_Total' not in df.columns:
        debug_print("[DEBUG] 'Engagement_Total' column missing. Calculating it.")
        df['Engagement_Total'] = (
            df['Views'].fillna(0) +
            df['Comments'].fillna(0) * 6 +
            df['Retweets'].fillna(0) * 3 +
            df['Likes'].fillna(0) * 2 +
            df['Bookmarks'].fillna(0)
        )
    else:
        debug_print("[DEBUG] 'Engagement_Total' column exists.")
    return df

def load_latest_csv(directories):
    """
    Carrega o CSV mais recente com base no timestamp no nome do arquivo.
    Retorna o DataFrame resultante e o nome do arquivo.
    """
    files = []
    for directory in directories:
        if not os.path.isdir(directory):
            debug_print(f"[WARNING] Directory not found: {directory}")
            continue
        dir_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".csv")]
        debug_print(f"[DEBUG] Found files in {directory}: {dir_files}")
        files.extend(dir_files)

    if not files:
        raise FileNotFoundError("No CSV files found in the specified directories.")

    # Seleciona o arquivo mais recente
    latest_file = max(files, key=lambda f: extract_datetime_from_filename(os.path.basename(f)))
    debug_print(f"[DEBUG] Latest file selected: {latest_file}")

    try:
        df = pd.read_csv(latest_file)
        debug_print(f"[DEBUG] File {latest_file} loaded successfully. Shape: {df.shape}")
        debug_print(f"[DEBUG] File head:\n{df.head()}")
        debug_print(f"[DEBUG] File columns: {df.columns.tolist()}")
    except Exception as e:
        debug_print(f"[ERROR] Failed to read {latest_file}: {e}")
        raise e

    # Garantir que 'Engagement_Total' exista
    df = ensure_engagement_total(df)
    df["Datetime"] = extract_datetime_from_filename(os.path.basename(latest_file))
    return df, latest_file

def load_latest_and_second_latest_csv(directories):
    """
    Carrega o CSV mais recente e o segundo mais recente.
    Retorna dois DataFrames e os nomes dos arquivos.
    """
    files = []
    for directory in directories:
        if not os.path.isdir(directory):
            debug_print(f"[WARNING] Directory not found: {directory}")
            continue
        dir_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".csv")]
        files.extend(dir_files)

    if len(files) < 2:
        raise FileNotFoundError("Less than two CSV files found in the specified directories.")

    # Ordena pelos timestamps decrescente
    sorted_files = sorted(files, key=lambda f: extract_datetime_from_filename(os.path.basename(f)), reverse=True)
    latest_file = sorted_files[0]
    second_latest_file = sorted_files[1]

    debug_print(f"[DEBUG] Loading latest CSV file: {latest_file}")
    debug_print(f"[DEBUG] Loading second latest CSV file: {second_latest_file}")

    latest_df = pd.read_csv(latest_file)
    latest_df = ensure_engagement_total(latest_df)
    latest_df["Datetime"] = extract_datetime_from_filename(os.path.basename(latest_file))

    second_latest_df = pd.read_csv(second_latest_file)
    second_latest_df = ensure_engagement_total(second_latest_df)
    second_latest_df["Datetime"] = extract_datetime_from_filename(os.path.basename(second_latest_file))

    return latest_df, second_latest_df, latest_file, second_latest_file

def load_week_data(week):
    """
    Carrega os dados para a semana específica (Week1, Week2, etc.).
    Retorna um DataFrame com os dados da semana selecionada.
    """
    try:
        debug_print(f"Selected week: {week}")
        directory = week_directories.get(week, None)
        debug_print(f"[DEBUG] Directory for {week}: {directory}")

        if not directory:
            raise FileNotFoundError(f"Directory for {week} not found.")
        if not os.path.isdir(directory):
            debug_print(f"[WARNING] Directory does not exist: {directory}")
            raise FileNotFoundError(f"Directory {directory} does not exist.")

        csv_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".csv")]
        debug_print(f"[DEBUG] Found {len(csv_files)} CSV files in {directory}: {csv_files}")

        if not csv_files:
            raise FileNotFoundError(f"No CSV files found in {directory} for {week}.")

        latest_file = max(csv_files, key=lambda f: extract_datetime_from_filename(os.path.basename(f)))
        debug_print(f"[DEBUG] Latest file selected for {week}: {latest_file}")

        df = pd.read_csv(latest_file)
        debug_print(f"[DEBUG] DataFrame loaded from {latest_file}. Shape: {df.shape}")
        debug_print(f"[DEBUG] File head:\n{df.head()}")
        debug_print(f"[DEBUG] File columns: {df.columns.tolist()}")

        df = ensure_engagement_total(df)
        df["Datetime"] = extract_datetime_from_filename(os.path.basename(latest_file))
        df["Date"] = df["Datetime"].dt.strftime("%d/%m %H:%M")

        return df

    except Exception as e:
        debug_print(f"[ERROR] Failed to load data for {week}: {e}")
        st.error(f"Error loading data for {week}: {e}")
        return pd.DataFrame()

# Carrega dados com base na seleção do usuário
if selected_week in ["Week1", "Week2", "Week3", "Week4"]:
    week_data = load_week_data(selected_week)
elif selected_week == "All Weeks":
    # Carrega dados de todas as semanas
    all_week_data = []
    for week, directory in week_directories.items():
        week_df = load_week_data(week)
        if not week_df.empty:
            week_df["Week"] = week
            all_week_data.append(week_df)
    week_data = pd.concat(all_week_data, ignore_index=True) if all_week_data else pd.DataFrame()
else:
    week_data = pd.DataFrame()

# Exibe uma mensagem se não houver dados
if week_data.empty:
    st.warning(f"No data available for {selected_week}.")
else:
    st.success(f"Data loaded successfully for {selected_week}!")
    debug_print(week_data.head())

def sum_weekly_data(weekly_data):
    """
    Concatena todos os DataFrames semanais em um único DataFrame.
    """
    if not weekly_data:
        raise ValueError("No weekly data to sum.")
    combined_df = pd.concat(weekly_data.values(), ignore_index=True)
    debug_print("[DEBUG] Combined weekly DataFrame:")
    debug_print(combined_df.head())
    debug_print(f"[DEBUG] Combined DataFrame shape: {combined_df.shape}")
    return combined_df

def load_all_csv_files(directories):
    """
    Carrega todos os CSVs em várias pastas, retornando um DataFrame combinado.
    """
    dataframes = []
    for directory in directories:
        if not os.path.isdir(directory):
            debug_print(f"[WARNING] Directory not found: {directory}")
            continue
        for file in os.listdir(directory):
            if file.endswith(".csv"):
                file_path = os.path.join(directory, file)
                debug_print(f"[DEBUG] Loading CSV file for all weeks: {file_path}")
                try:
                    df = pd.read_csv(file_path)
                    df = ensure_engagement_total(df)
                    df["Datetime"] = extract_datetime_from_filename(file)
                    df["Date"] = df["Datetime"].dt.strftime("%d/%m %H:%M")
                    dataframes.append(df)
                except Exception as e:
                    debug_print(f"[ERROR] Failed to load {file_path}: {e}")
    if not dataframes:
        raise FileNotFoundError("No CSV files found in the specified directories.")
    combined_df = pd.concat(dataframes, ignore_index=True)
    debug_print("[DEBUG] Combined DataFrame for all CSV files:")
    debug_print(combined_df.head())
    debug_print(f"[DEBUG] Combined DataFrame shape: {combined_df.shape}")
    debug_print(f"[DEBUG] Columns: {combined_df.columns}")
    debug_print(f"[DEBUG] Data types: {combined_df.dtypes}")
    return combined_df

def calculate_differences(latest_df, second_latest_df):
    """
    Calcula as diferenças absolutas e percentuais entre o CSV mais recente e o segundo mais recente.
    """
    metrics = ["Likes", "Retweets", "Comments", "Bookmarks", "Views", "Engagement_Total"]
    differences = {}
    for metric in metrics:
        latest_total = latest_df[metric].sum()
        if second_latest_df is not None and metric in second_latest_df.columns:
            second_latest_total = second_latest_df[metric].sum()
        else:
            second_latest_total = 0
        abs_diff = latest_total - second_latest_total
        perc_diff = (abs_diff / second_latest_total * 100) if second_latest_total != 0 else 0
        differences[metric] = {
            "latest_total": latest_total,
            "abs_diff": abs_diff,
            "perc_diff": perc_diff,
        }
        debug_print(
            f"[DEBUG] Metric: {metric}, "
            f"Latest: {latest_total}, "
            f"Second Latest: {second_latest_total}, "
            f"Diff: {abs_diff}, "
            f"% Diff: {perc_diff}"
        )
    return differences

def display_summary_metrics(latest_df, second_latest_df, differences):
    """
    Exibe métricas de resumo usando os componentes 'metric' do Streamlit.
    """
    col1, col2, col3 = st.columns(3)
    col4, col5, col6 = st.columns(3)
    col7, col8, col9 = st.columns(3)  # col9 para Unique Users

    def format_metric(current, diff):
        return f"{current:,}", f"{diff:+,}"

    # Total Likes
    total_likes = latest_df["Likes"].sum()
    likes_diff = differences["Likes"]["abs_diff"]
    col1.metric("Total Likes", *format_metric(total_likes, likes_diff))

    # Total Retweets
    total_retweets = latest_df["Retweets"].sum()
    retweets_diff = differences["Retweets"]["abs_diff"]
    col2.metric("Total Retweets", *format_metric(total_retweets, retweets_diff))

    # Total Comments
    total_comments = latest_df["Comments"].sum()
    comments_diff = differences["Comments"]["abs_diff"]
    col3.metric("Total Comments", *format_metric(total_comments, comments_diff))

    # Total Bookmarks
    total_bookmarks = latest_df["Bookmarks"].sum()
    bookmarks_diff = differences["Bookmarks"]["abs_diff"]
    col4.metric("Total Bookmarks", *format_metric(total_bookmarks, bookmarks_diff))

    # Total Views
    total_views = latest_df["Views"].sum()
    views_diff = differences["Views"]["abs_diff"]
    col5.metric("Total Views", *format_metric(total_views, views_diff))

    # Total Engagement
    total_engagement = latest_df["Engagement_Total"].sum()
    engagement_diff = differences["Engagement_Total"]["abs_diff"]
    col6.metric("Total Engagement", *format_metric(total_engagement, engagement_diff))

    # Total Posts
    total_posts = len(latest_df)
    total_posts_diff = total_posts - len(second_latest_df) if second_latest_df is not None else 0
    col7.metric("Total Posts", f"{total_posts:,}", f"{total_posts_diff:+,}")

    # Average Engagement per Post
    avg_engagement = latest_df["Engagement_Total"].mean()
    if second_latest_df is not None:
        avg_engagement_diff = avg_engagement - second_latest_df["Engagement_Total"].mean()
    else:
        avg_engagement_diff = 0
    col8.metric("Average Engagement per Post", f"{avg_engagement:.2f}", f"{avg_engagement_diff:+.2f}")

    # Unique Users
    unique_users = latest_df["User"].str.strip().str.lower().nunique()
    col9.metric("Unique Users", f"{unique_users:,}")

def display_full_ranking(df):
    """
    Exibe o ranking completo em uma tabela.
    """
    st.header("Ranking")
    columns_order = ["User", "Engagement_Total", "Views", "Likes", "Retweets", "Comments", "Bookmarks", "Link"]
    if all(col in df.columns for col in columns_order):
        df_sorted = df[columns_order].sort_values(by="Engagement_Total", ascending=False).reset_index(drop=True)
        st.dataframe(df_sorted)
    else:
        missing_cols = [col for col in columns_order if col not in df.columns]
        st.error(f"The DataFrame is missing the following columns required for ranking: {missing_cols}")

def clean_dataframe(df):
    """
    Limpa o DataFrame removendo colunas inválidas, NaNs e duplicados.
    """
    debug_print("\n[DEBUG] Cleaning DataFrame...")

    invalid_cols = [col for col in df.columns if "HEAD" in col or col.isspace()]
    if invalid_cols:
        debug_print(f"[DEBUG] Removing invalid columns: {invalid_cols}")
        df = df.drop(columns=invalid_cols, errors="ignore")

    critical_columns = [col for col in ["Date", "User", "Engagement_Total"] if col in df.columns]
    debug_print(f"[DEBUG] Valid critical columns for cleaning: {critical_columns}")

    if critical_columns:
        df = df.dropna(subset=critical_columns)

    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].str.strip().str.replace(r"<<<<<<< HEAD", "", regex=True)

    duplicated_rows = df.duplicated().sum()
    if duplicated_rows > 0:
        debug_print(f"[DEBUG] Removing {duplicated_rows} duplicated rows.")
        df = df.drop_duplicates()

    debug_print("[DEBUG] DataFrame after cleaning:")
    debug_print(df.head())
    debug_print(f"[DEBUG] Shape: {df.shape}")
    debug_print(f"[DEBUG] Data types: {df.dtypes}")
    if "User" in df.columns:
        debug_print(f"[DEBUG] Unique values in 'User': {df['User'].unique()[:10]}")

    return df

def plot_engagement_by_all_users_and_date(df, user_order=None):
    """
    Plota o engajamento de todos os usuários ao longo do tempo,
    com a legenda de usuários ordenada conforme ranking.
    """
    df = clean_dataframe(df)
    df["User"] = df["User"].str.strip().str.lower()

    df["Datetime"] = pd.to_datetime(df["Date"], format="%d/%m %H:%M", errors="coerce")
    df = df.dropna(subset=["Datetime"])
    df = df.sort_values(by="Datetime")

    grouped_df = df.groupby(["Datetime", "User"], as_index=False).agg({"Engagement_Total": "sum"})
    pivot_df = grouped_df.pivot(index="Datetime", columns="User", values="Engagement_Total").fillna(0)

    if user_order:
        sorted_users = user_order
    else:
        ranking = (
            df.groupby("User")["Engagement_Total"]
            .sum()
            .sort_values(ascending=False)
        )
        sorted_users = ranking.index.tolist()

    pivot_df = pivot_df[sorted_users]

    fig = go.Figure()
    for idx, user in enumerate(sorted_users):
        visibility = True if idx < 10 else "legendonly"
        fig.add_trace(go.Scatter(
            x=pivot_df.index,
            y=pivot_df[user],
            mode="lines+markers",
            name=user,
            visible=visibility,
        ))

    fig.update_layout(
        title="Engagement by User (Top 10 Initially, All Users in Legend)",
        xaxis_title="Date",
        yaxis_title="Total Engagement",
        legend_title="Users (Ranked)",
        xaxis_tickformat="%d/%m %H:%M",
        xaxis_tickangle=-45,
        autosize=False,
        width=1600,
        height=900,
        margin=dict(l=40, r=40, t=50, b=100),
    )

    st.plotly_chart(fig, use_container_width=True)

def plot_engagement_components_from_latest_csv(latest_df):
    """
    Plota a composição do engajamento (Comments, Retweets, Likes, Bookmarks) para os 25 usuários no topo.
    """
    engagement_metrics = latest_df.groupby("User")[["Comments", "Retweets", "Likes", "Bookmarks"]].sum()

    top_users = engagement_metrics.sum(axis=1).sort_values(ascending=False).head(25).index
    filtered_metrics = engagement_metrics.loc[top_users]

    metrics = ["Comments", "Retweets", "Likes", "Bookmarks"]
    colors = ["#636EFA", "#EF553B", "#00CC96", "#AB63FA"]

    fig = go.Figure()
    for metric, color in zip(metrics, colors):
        fig.add_trace(go.Bar(
            x=filtered_metrics.index,
            y=filtered_metrics[metric],
            name=metric,
            marker_color=color,
            text=[f"{metric[0]}={int(value)}" if value > 0 else "" for value in filtered_metrics[metric]],
            textposition='inside',
            textfont=dict(color='black', size=9),
            hoverinfo='y+name'
        ))

    fig.update_layout(
        barmode='stack',
        title="Engagement Components of Top 25",
        xaxis_title="User",
        yaxis_title="Quantity",
        xaxis_tickangle=-45,
        legend_title="Metric",
        autosize=False,
        width=1600,
        height=900,
        margin=dict(l=40, r=40, t=50, b=100),
    )

    st.plotly_chart(fig, use_container_width=True)

def plot_engagement_total_by_rank(df):
    """
    Plota o total de engajamento (scatter) ordenado por ranking.
    """
    sorted_df = df.groupby("User", as_index=False)["Engagement_Total"] \
                  .sum() \
                  .sort_values(by="Engagement_Total", ascending=False) \
                  .reset_index(drop=True)
    sorted_df["Rank"] = sorted_df.index + 1

    fig = px.scatter(
        sorted_df,
        x="Rank",
        y="Engagement_Total",
        color="Engagement_Total",
        color_continuous_scale='Viridis',
        labels={"Rank": "Position", "Engagement_Total": "Total Engagement"},
        title="Total Engagement by Ranking Order",
    )

    fig.update_layout(
        autosize=False,
        width=1600,
        height=900,
        margin=dict(l=40, r=40, t=50, b=100),
    )

    st.plotly_chart(fig, use_container_width=True)

def plot_likes_ranking(latest_df):
    """
    Plota um ranking de 'Likes' para os 25 usuários no topo.
    """
    likes_ranking = latest_df.groupby("User")["Likes"].sum().reset_index().sort_values(by="Likes", ascending=False).head(25)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=likes_ranking["User"],
        y=likes_ranking["Likes"],
        marker_color='skyblue',
        text=likes_ranking["Likes"],
        textposition='outside',
    ))

    fig.update_layout(
        title="Likes Ranking (Top 25)",
        xaxis_title="Users",
        yaxis_title="Number of Likes",
        xaxis_tickangle=-45,
        width=1600,
        height=900,
        margin=dict(l=40, r=40, t=50, b=100),
    )

    st.plotly_chart(fig, use_container_width=True)

def plot_views_ranking(latest_df):
    """
    Plota um ranking de 'Views' para os 25 usuários no topo.
    """
    views_ranking = latest_df.groupby("User")["Views"].sum().reset_index().sort_values(by="Views", ascending=False).head(25)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=views_ranking["User"],
        y=views_ranking["Views"],
        marker_color='orange',
        text=views_ranking["Views"],
        textposition='outside',
    ))

    fig.update_layout(
        title="Views Ranking (Top 25)",
        xaxis_title="Users",
        yaxis_title="Number of Views",
        xaxis_tickangle=-45,
        width=1600,
        height=900,
        margin=dict(l=40, r=40, t=50, b=100),
    )

    st.plotly_chart(fig, use_container_width=True)

def plot_engagement_total_by_date(directories):
    """
    Plota o engajamento total por data, obtendo dados de todos os CSVs nos diretórios informados.
    """
    engagement_data = []
    for directory in directories:
        if not os.path.isdir(directory):
            debug_print(f"[WARNING] Directory not found: {directory}")
            continue
        files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".csv")]
        if not files:
            debug_print(f"[WARNING] No CSV files found in {directory}.")
            continue
        for file in files:
            debug_print(f"[DEBUG] Processing file for total engagement by date: {file}")
            try:
                df = pd.read_csv(file)
                df = ensure_engagement_total(df)
                total_engagement = df["Engagement_Total"].sum()
                date = extract_datetime_from_filename(os.path.basename(file))
                if pd.isna(date):
                    debug_print(f"[WARNING] Invalid date extracted from filename: {file}. Skipping.")
                    continue
                engagement_data.append({"Date": date, "Total_Engagement": total_engagement})
            except Exception as e:
                debug_print(f"[ERROR] Failed to process {file}: {e}")

    if not engagement_data:
        st.warning("No data available to plot Total Engagement by Date.")
        return

    engagement_df = pd.DataFrame(engagement_data).sort_values(by="Date")
    debug_print("[DEBUG] Engagement DataFrame for Total Engagement by Date:")
    debug_print(engagement_df.head())

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=engagement_df["Date"],
        y=engagement_df["Total_Engagement"],
        mode='lines+markers',
        line=dict(color='green'),
    ))

    fig.update_layout(
        title="Total Engagement by Date",
        xaxis_title="Date",
        yaxis_title="Total Engagement",
        xaxis_tickangle=-45,
        autosize=False,
        width=1600,
        height=900,
        margin=dict(l=40, r=40, t=50, b=100),
    )

    st.plotly_chart(fig, use_container_width=True)

def plot_top_post_by_user(df):
    """
    Plota o post de maior engajamento para cada usuário (bar chart).
    """
    df = clean_dataframe(df)
    df["User"] = df["User"].str.strip().str.lower()

    top_posts = df.loc[df.groupby("User")["Engagement_Total"].idxmax()]
    top_posts = top_posts.sort_values(by="Engagement_Total", ascending=False)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=top_posts["User"],
        y=top_posts["Engagement_Total"],
        text=top_posts["Engagement_Total"],
        textposition='auto',
    ))

    fig.update_layout(
        title="Top Post by Engagement for Each User",
        xaxis_title="User",
        yaxis_title="Engagement Total",
        xaxis_tickangle=-45,
        autosize=False,
        width=1600,
        height=900,
        margin=dict(l=40, r=40, t=50, b=100),
    )

    st.plotly_chart(fig, use_container_width=True)

# Bloco principal de execução
try:
    if selected_week == 'All Weeks':
        # Exibir dados consolidados
        latest_df = week_data
        second_latest_df = None
        differences = calculate_differences(latest_df, second_latest_df)
        timestamp = time.strftime("%d/%m/%Y %H:%M:%S")
    else:
        # Carrega CSV mais recente e segundo mais recente para a semana selecionada
        latest_df, second_latest_df, latest_file, second_latest_file = load_latest_and_second_latest_csv(CSV_DIRS)
        differences = calculate_differences(latest_df, second_latest_df)
        timestamp = extract_datetime_from_filename(os.path.basename(latest_file)).strftime("%d/%m/%Y %H:%M:%S")

except FileNotFoundError as e:
    st.error(f"Error: {e}")
    st.stop()
except Exception as e:
    st.error(f"An unexpected error occurred: {e}")
    st.stop()

# Para semanas individuais, recarrega o CSV mais recente
if selected_week != 'All Weeks':
    try:
        latest_df, latest_file = load_latest_csv(CSV_DIRS)
        latest_df["User"] = latest_df["User"].str.strip().str.lower()
        timestamp = extract_datetime_from_filename(os.path.basename(latest_file)).strftime("%d/%m/%Y %H:%M:%S")
    except Exception as e:
        st.error(f"Error loading latest CSV: {e}")
        st.stop()

latest_ranking = (
    latest_df.groupby("User")["Engagement_Total"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .index.tolist()
)

user_order = latest_df['User'].drop_duplicates().tolist()

st.write(
    f"<p style='text-align: center; font-size: 12px;'><strong>LAST UPDATE:</strong> {timestamp}</p>",
    unsafe_allow_html=True
)

# Exibe métricas de resumo
display_summary_metrics(latest_df, second_latest_df, differences)

# Se selecionar "All Weeks", não mostra os gráficos detalhados
if selected_week != 'All Weeks':
    # Carrega todos os CSVs para plotar evolução
    all_data_df = load_all_csv_files(CSV_DIRS)

    # Top 10 usuários por engajamento
    ranking = (
        latest_df.groupby("User")["Engagement_Total"]
        .sum()
        .sort_values(ascending=False)
    )
    top_10_users = ranking.head(10).index.tolist()
    top_10_users = [user.strip().lower() for user in top_10_users]

    st.header("Engagement by User (Top 10)")
    try:
        plot_engagement_by_all_users_and_date(all_data_df, user_order=user_order)
    except Exception as e:
        st.error(f"Error plotting Engagement by User (Top 10): {e}")

    st.header("Engagement of Top 25 (Components)")
    try:
        plot_engagement_components_from_latest_csv(latest_df)
    except Exception as e:
        st.error(f"Error plotting Engagement Components: {e}")

    st.header("Total Engagement by Ranking Order")
    try:
        plot_engagement_total_by_rank(latest_df)
    except Exception as e:
        st.error(f"Error plotting Total Engagement by Rank: {e}")

    st.header("Likes Ranking (Top 25)")
    try:
        plot_likes_ranking(latest_df)
    except Exception as e:
        st.error(f"Error plotting Likes Ranking: {e}")

    st.header("Views Ranking (Top 25)")
    try:
        plot_views_ranking(latest_df)
    except Exception as e:
        st.error(f"Error plotting Views Ranking: {e}")

    st.header("Total Engagement by Date")
    try:
        plot_engagement_total_by_date(CSV_DIRS)
    except Exception as e:
        st.error(f"Error plotting Total Engagement by Date: {e}")

    plot_top_post_by_user(latest_df)
    display_full_ranking(latest_df)

# Fórmula do engajamento
st.write("Total Engagement = Views + (Comments x 6) + (Retweets x 3) + (Likes x 2) + (Bookmarks).")
