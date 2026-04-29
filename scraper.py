# scraper.py - v1.6.0
import requests
import pandas as pd
import os
import html
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÕES GERAIS
# ==========================================
ARQUIVO_CSV = 'data/noticias_if.csv'
DATA_LIMITE = '2024-01-01' # O robô não pegará nada anterior a isso

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
# 2. EXTRAÇÃO COM TRAVA TEMPORAL
# ==========================================
def extrair_noticias():
    noticias_coletadas = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    for unidade in UNIDADES:
        urls_para_testar = [unidade['url']]
        if unidade['id'] == 'Reitoria':
            urls_para_testar.append("https://ifbaiano.edu.br/portal/wp-json/wp/v2/posts/")
            urls_para_testar.append("https://www.ifbaiano.edu.br/wp-json/wp/v2/posts/")

        sucesso_na_unidade = False

        for base_url in urls_para_testar:
            if sucesso_na_unidade:
                break
                
            print(f"Coletando: {unidade['id']} | URL: {base_url}...")
            pagina = 1
            limite_atingido = False

            while not limite_atingido:
                try:
                    url = f"{base_url}?per_page=100&page={pagina}"
                    response = requests.get(url, headers=headers, timeout=20)
                    
                    if response.status_code != 200:
                        break
                        
                    posts = response.json()
                    if not posts or not isinstance(posts, list):
                        break 

                    for post in posts:
                        data_limpa = post.get('date', '').split('T')[0]
                        
                        # Trava temporal: Se a notícia for mais velha que 2024, paramos
                        if data_limpa < DATA_LIMITE:
                            limite_atingido = True
                            break

                        titulo_limpo = html.unescape(post.get('title', {}).get('rendered', 'Sem Título'))
                        noticias_coletadas.append({
                            'campus': unidade['id'],
                            'titulo': titulo_limpo,
                            'link': post.get('link', ''),
                            'data': data_limpa
                        })
                    
                    if not limite_atingido:
                        print(f"   ✓ Página {pagina} processada.")
                        pagina += 1
                        
                except Exception as e:
                    print(f"   X Erro na página {pagina}: {e}")
                    break 

            if len(noticias_coletadas) > 0:
                sucesso_na_unidade = True

    return pd.DataFrame(noticias_coletadas)

# ==========================================
# 3. SALVAMENTO INCREMENTAL
# ==========================================
def limpar_e_salvar_dados(df_novo):
    if df_novo.empty:
        print("Nenhum dado novo retornado.")
        return

    df_novo = df_novo.dropna(subset=['data'])
    os.makedirs(os.path.dirname(ARQUIVO_CSV), exist_ok=True)

    if os.path.exists(ARQUIVO_CSV):
        print("Atualizando histórico incremental...")
        df_existente = pd.read_csv(ARQUIVO_CSV)
        df_final = pd.concat([df_existente, df_novo], ignore_index=True)
        # Mantém a última versão e evita duplicatas absolutas
        df_final = df_final.drop_duplicates(subset=['link'], keep='last')
    else:
        print("Criando banco de dados...")
        df_final = df_novo

    # Ordenação decrescente antes de salvar
    df_final = df_final.sort_values(by='data', ascending=False)
    df_final.to_csv(ARQUIVO_CSV, index=False, encoding='utf-8')
    print(f"Sucesso! Banco atualizado. Total de notícias: {len(df_final)}")

# ==========================================
# 4. EXECUÇÃO
# ==========================================
if __name__ == "__main__":
    print("Iniciando Painel DICOM v1.6.0...")
    df_dados = extrair_noticias()
    limpar_e_salvar_dados(df_dados)
    print("Processo v1.6.0 finalizado.")
