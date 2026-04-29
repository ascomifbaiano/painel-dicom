import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÕES GERAIS
# ==========================================
ARQUIVO_CSV = 'data/noticias_if.csv'

# Exemplo de lista de sites para varrer (pode ser expandida para os 18 campi)
SITES_ALVO = [
    {"campus": "Reitoria", "url": "https://ifbaiano.edu.br/portal/noticias/"},
    {"campus": "Bom Jesus da Lapa", "url": "https://ifbaiano.edu.br/portal/lapa/noticias/"}
]

# ==========================================
# 2. FUNÇÃO DE EXTRAÇÃO (WEB SCRAPING)
# ==========================================
def extrair_noticias():
    noticias_raspadas = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    for site in SITES_ALVO:
        try:
            print(f"Acessando: {site['campus']}...")
            response = requests.get(site['url'], headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # ATENÇÃO: As classes HTML abaixo ('article.noticia', 'h2.titulo', etc.) 
            # precisam ser ajustadas de acordo com o código fonte real do site do IF Baiano.
            artigos = soup.find_all('article', class_='category-noticias') # Exemplo genérico WordPress

            for artigo in artigos:
                titulo_tag = artigo.find('h2')
                link_tag = artigo.find('a')
                data_tag = artigo.find('time') # ou span com a data

                if titulo_tag and link_tag and data_tag:
                    noticias_raspadas.append({
                        'campus': site['campus'],
                        'titulo': titulo_tag.get_text(strip=True),
                        'link': link_tag['href'],
                        'data_bruta': data_tag.get_text(strip=True) # Ex: "29 de Abril de 2026" ou "29/04/2026"
                    })
        except Exception as e:
            print(f"Erro ao acessar {site['campus']}: {e}")

    return pd.DataFrame(noticias_raspadas)

# ==========================================
# 3. FUNÇÃO DE LIMPEZA E PADRONIZAÇÃO (ENGENHARIA DE DADOS)
# ==========================================
def limpar_e_salvar_dados(df_novo):
    if df_novo.empty:
        print("Nenhuma notícia nova encontrada na extração de hoje.")
        return

    # DESAFIO 2: Garantir que a data esteja em AAAA-MM-DD
    # Converte a coluna de data (assumindo que no site ela vem como DD/MM/AAAA)
    # O parâmetro dayfirst=True é crucial para datas brasileiras
    df_novo['data'] = pd.to_datetime(df_novo['data_bruta'], format='%d/%m/%Y', errors='coerce').dt.strftime('%Y-%m-%d')
    
    # Removemos a coluna bruta, pois o Dashboard só precisa da data formatada
    df_novo = df_novo.drop(columns=['data_bruta'])

    # Cria a pasta 'data' se ela não existir
    os.makedirs(os.path.dirname(ARQUIVO_CSV), exist_ok=True)

    # DESAFIO 3: Lógica de Deduplicação
    if os.path.exists(ARQUIVO_CSV):
        print("Arquivo CSV existente encontrado. Iniciando mesclagem e deduplicação...")
        df_existente = pd.read_csv(ARQUIVO_CSV)
        
        # Junta os dados antigos com os que acabamos de raspar
        df_final = pd.concat([df_existente, df_novo], ignore_index=True)
        
        # Remove as duplicatas usando o 'link' como identificador único (a chave primária)
        # O keep='last' garante que, se uma notícia foi atualizada, ficamos com a versão mais recente
        df_final = df_final.drop_duplicates(subset=['link'], keep='last')
    else:
        print("Arquivo CSV não encontrado. Criando o primeiro banco de dados...")
        df_final = df_novo

    # DESAFIO 1: Exportar os dados em CSV estruturado
    df_final.to_csv(ARQUIVO_CSV, index=False, encoding='utf-8')
    print(f"Sucesso! Banco de dados atualizado. Total de registros: {len(df_final)}")

# ==========================================
# 4. EXECUÇÃO PRINCIPAL
# ==========================================
if __name__ == "__main__":
    print("Iniciando Radar de Notícias...")
    df_dados_novos = extrair_noticias()
    limpar_e_salvar_dados(df_dados_novos)
    print("Pipeline finalizado.")
