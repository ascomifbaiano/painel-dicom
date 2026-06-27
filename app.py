import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Performance DICOM | IF Baiano", layout="wide", page_icon="📊")

# Cabeçalho
st.title("📊 Painel de Performance - DICOM")
st.markdown("Monitoramento em tempo real das publicações dos campi do IF Baiano.")

@st.cache_data
def carregar_dados():
    try:
        df = pd.read_csv("data/noticias_if.csv")
        df['data'] = pd.to_datetime(df['data'])
        return df.sort_values(by='data', ascending=False) 
    except FileNotFoundError:
        st.error("Banco de dados não encontrado. Aguarde a primeira execução do Radar.")
        return pd.DataFrame()

df = carregar_dados()

if not df.empty:
    st.sidebar.header("Filtros")
    campi_disponiveis = df['campus'].unique()
    campus_selecionado = st.sidebar.multiselect("Selecione o Campus:", options=campi_disponiveis, default=campi_disponiveis)
    
    df_filtrado = df[df['campus'].isin(campus_selecionado)]

    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Publicações (Período)", len(df_filtrado))
    campus_mais_ativo = df_filtrado['campus'].value_counts().idxmax() if len(df_filtrado) > 0 else "-"
    col2.metric("Campus mais Ativo", campus_mais_ativo)
    col3.metric("Última Atualização do Radar", df['data'].max().strftime('%d/%m/%Y'))

    st.divider()

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Publicações por Campus")
        contagem_campus = df_filtrado['campus'].value_counts().reset_index()
        contagem_campus.columns = ['Campus', 'Total']
        fig_barra = px.bar(contagem_campus, x='Campus', y='Total', 
                           color_discrete_sequence=['#3E9A2D'], text_auto=True)
        fig_barra.update_layout(xaxis_title="", yaxis_title="Publicações")
        st.plotly_chart(fig_barra, use_container_width=True)

    with c2:
        st.subheader("Linha do Tempo (Volume de Publicações)")
        contagem_tempo = df_filtrado.groupby('data').size().reset_index(name='Publicações')
        fig_linha = px.line(contagem_tempo, x='data', y='Publicações', line_shape='spline', markers=True)
        fig_linha.update_traces(line_color='#3E9A2D', marker_color='#C80710')
        fig_linha.update_layout(xaxis_title="", yaxis_title="Publicações")
        st.plotly_chart(fig_linha, use_container_width=True)

    st.divider()
    st.subheader("Últimas Notícias")
    st.dataframe(
        df_filtrado[['data', 'campus', 'titulo', 'link']].head(15),
        column_config={
            "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
            "campus": "Campus",
            "titulo": "Título da Notícia",
            "link": st.column_config.LinkColumn("Acessar Link")
        },
        hide_index=True,
        use_container_width=True
    )
