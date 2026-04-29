import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Performance DICOM | IF Baiano", layout="wide", page_icon="📊")

# Cabeçalho
st.title("📊 Painel de Performance - DICOM")
st.markdown("Monitoramento em tempo real das publicações dos campi do IF Baiano.")

# Função para carregar os dados
@st.cache_data
def carregar_dados():
    try:
        df = pd.read_csv("data/noticias_if.csv")
        df['data'] = pd.to_datetime(df['data'])
        # Ordena da mais recente para a mais antiga
        df = df.sort_values(by='data', ascending=False) 
        return df
    except FileNotFoundError:
        st.error("Banco de dados não encontrado. Aguarde a primeira execução do Radar.")
        return pd.DataFrame()

df = carregar_dados()

if not df.empty:
    # Sidebar de Filtros
    st.sidebar.header("Filtros")
    campi_disponiveis = df['campus'].unique()
    campus_selecionado = st.sidebar.multiselect("Selecione o Campus:", options=campi_disponiveis, default=campi_disponiveis)
    
    # Aplica o filtro
    df_filtrado = df[df['campus'].isin(campus_selecionado)]

    # Indicadores principais (Cards)
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Publicações (Período)", len(df_filtrado))
    
    if len(df_filtrado) > 0:
        campus_mais_ativo = df_filtrado['campus'].value_counts().idxmax()
        col2.metric("Campus mais Ativo", campus_mais_ativo)
    else:
        col2.metric("Campus mais Ativo", "-")
        
    col3.metric("Última Atualização do Radar", df['data'].max().strftime('%d/%m/%Y'))

    st.divider()

    # Gráficos
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Publicações por Campus")
        contagem_campus = df_filtrado['campus'].value_counts().reset_index()
        contagem_campus.columns = ['Campus', 'Total']
        fig_barra = px.bar(contagem_campus, x='Campus', y='Total', 
                           color_discrete_sequence=['#2E8B57'], text_auto=True)
        st.plotly_chart(fig_barra, use_container_width=True)

    with c2:
        st.subheader("Linha do Tempo (Volume de Publicações)")
        contagem_tempo = df_filtrado.groupby('data').size().reset_index(name='Publicações')
        fig_linha = px.line(contagem_tempo, x='data', y='Publicações', line_shape='spline', markers=True)
        fig_linha.update_traces(line_color='#2E8B57')
        st.plotly_chart(fig_linha, use_container_width=True)

    # Tabela com as últimas notícias
    st.divider()
    st.subheader("Últimas Notícias")
    # Mostra um dataframe bonitinho na tela
    st.dataframe(
        df_filtrado[['data', 'campus', 'titulo', 'link']].head(10),
        column_config={
            "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
            "campus": "Campus",
            "titulo": "Título da Notícia",
            "link": st.column_config.LinkColumn("Acessar Link")
        },
        hide_index=True,
        use_container_width=True
    )
