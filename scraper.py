# scraper.py - v1.1.0
import requests
import pandas as pd
import os
import html

# ==========================================
# 1. CONFIGURAÇÕES GERAIS
# ==========================================
ARQUIVO_CSV = 'data/noticias_if.csv'

# Lista das unidades consumindo a API REST do WordPress
UNIDADES = [
    { "id": "Reitoria", "url": "https://www.ifbaiano.edu.br/portal/wp-json/wp/v2/posts/" },
    { "id": "Alagoinhas", "url": "https://www.ifbaiano.edu.br/unidades/alagoinhas/wp-json/wp/v2/posts/" },
    { "id": "Lapa", "url": "https://www.ifbaiano.edu.br/unidades/lapa/wp-json/wp/v2/posts/" },
    { "id": "Catu", "url": "https://www.ifbaiano.edu.br/unidades/catu/wp-json/wp/v2/posts/" },
    { "id": "Mangabeira", "url": "https://www.ifbaiano.edu.br/unidades/gmb/wp-json/wp/v2/posts/" },
    { "id": "Guanambi", "url": "https://www.ifbaiano.edu.br/unidades/guanambi/wp-json/wp/v2/posts/" },
    { "id": "Itaberaba", "url": "https://www.ifbaiano.edu.br/unidades/itaberaba/wp-json/wp/v2/posts/" },
    { "id": "Itapetinga", "url": "https://www.ifbaiano.edu.br/unidades/itapetinga/wp-json/wp/v2/posts/" },
    { "id": "Santa Inês", "url": "https://www.ifbaiano.edu.br/unidades/santaines/wp-json/wp/v2/posts/" },
    { "id": "Bonfim", "url": "https://www.ifbaiano.edu.br/unidades/bonfim/wp-json/wp/v2/posts/" },
    { "id": "Serrinha", "url": "https://www.ifbaiano.edu.br/unidades/serrinha/wp-json/wp/v2/posts/" },
    { "id": "Teixeira", "url": "https://www.ifbaiano.edu.br/unidades/teixeira/wp-json/wp/v2/posts/" },
    { "id": "Uruçuca", "url": "https://www.ifbaiano.edu.br/unidades/urucuca/wp-json/wp/v2/posts/" },
    { "id": "Valença", "url": "https://www.ifbaiano.edu.br/unidades/valenca/wp-json/wp/v2/posts/" },
    { "id": "Xique-Xique", "url": "https://www.ifbaiano.edu.br/unidades/xique-xique/wp-json/wp/v2/posts/" }
]

# ==========================================
# 2. FUNÇÃO DE EXTRAÇÃO (API REST)
# ==========================================
def extrair_noticias():
    noticias_coletadas = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    for unidade in UNIDADES:
        try:
            print(f"Coletando via API: {unidade['id']}...")
            # O parâmetro per_page=20 traz as 20 últimas notícias de cada campus de uma vez
            response = requests.get(f"{unidade['url']}?per_page=20", headers=headers, timeout=15)
            response.raise_for_status()
            
            # Lê o JSON retornado pela API
            posts = response.json()

            for post in posts:
                # O WordPress retorna a data no formato ISO "YYYY-MM-DDTHH:MM:SS"
                data_limpa = post.get('date', '').split('T')[0]
                
                # Decodifica entidades HTML do título (ex: &#8211; vira um traço normal)
                titulo_limpo = html.unescape(post.get('title', {}).get('rendered', 'Sem Título'))

                noticias_coletadas.append({
                    'campus': unidade['id'],
                    'titulo': titulo_limpo,
                    'link': post.get('link', ''),
                    'data': data_limpa
                })
        except Exception as e:
            print(f"Erro na API de {unidade['id']}: {e}")

    return pd.DataFrame(noticias_coletadas)

# ==========================================
# 3. FUNÇÃO DE LIMPEZA E SALVAMENTO
# ==========================================
def limpar_e_salvar_dados(df_novo):
    if df_novo.empty:
        print("Nenhum dado retornado pelas APIs.")
        return

    # Garante que as linhas sem data válida sejam removidas
    df_novo = df_novo.dropna(subset=['data'])

    os.makedirs(os.path.dirname(ARQUIVO_CSV), exist_ok=True)

    # Upsert: Mescla com o histórico e remove duplicatas baseadas no link
    if os.path.exists(ARQUIVO_CSV):
        print("Sincronizando com o banco de dados existente...")
        df_existente = pd.read_csv(ARQUIVO_CSV)
        df_final = pd.concat([df_existente, df_novo], ignore_index=True)
        df_final = df_final.drop_duplicates(subset=['link'], keep='last')
    else:
        print("Iniciando novo banco de dados...")
        df_final = df_novo

    # Ordena cronologicamente antes de salvar
    df_final = df_final.sort_values(by='data', ascending=False)
    
    df_final.to_csv(ARQUIVO_CSV, index=False, encoding='utf-8')
    print(f"Sucesso! CSV Atualizado. Total de registros globais: {len(df_final)}")

# ==========================================
# 4. EXECUÇÃO
# ==========================================
if __name__ == "__main__":
    print("Iniciando Radar de Notícias DICOM v1.1.0...")
    df_dados = extrair_noticias()
    limpar_e_salvar_dados(df_dados)
    print("Processo finalizado.")
