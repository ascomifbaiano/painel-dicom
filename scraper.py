# scraper.py - v1.3.0
import requests
import pandas as pd
import os
import html

# ==========================================
# 1. CONFIGURAÇÕES GERAIS
# ==========================================
ARQUIVO_CSV = 'data/noticias_if.csv'

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
# 2. FUNÇÃO DE EXTRAÇÃO COM PAGINAÇÃO E FALLBACK
# ==========================================
def extrair_noticias():
    noticias_coletadas = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    for unidade in UNIDADES:
        # Sistema de Fallback exclusivo para a Reitoria
        urls_para_testar = [unidade['url']]
        if unidade['id'] == 'Reitoria':
            # Adiciona rotas alternativas caso a principal falhe
            urls_para_testar.append("https://ifbaiano.edu.br/portal/wp-json/wp/v2/posts/")
            urls_para_testar.append("https://www.ifbaiano.edu.br/wp-json/wp/v2/posts/")

        sucesso_na_unidade = False

        for base_url in urls_para_testar:
            if sucesso_na_unidade:
                break
                
            print(f"Coletando via API: {unidade['id']} | Tentando URL: {base_url}...")
            
            pagina = 1
            max_paginas = 5 # Puxa até 5 páginas (500 notícias por campus)

            while pagina <= max_paginas:
                try:
                    # Paginação ativada: traz 100 por vez
                    url = f"{base_url}?per_page=100&page={pagina}"
                    response = requests.get(url, headers=headers, timeout=20)
                    
                    # Se retornar erro (ex: página não existe), encerra o loop dessa unidade
                    if response.status_code != 200:
                        break
                        
                    posts = response.json()

                    if not posts or not isinstance(posts, list):
                        break # Acabaram as notícias

                    for post in posts:
                        data_limpa = post.get('date', '').split('T')[0]
                        titulo_limpo = html.unescape(post.get('title', {}).get('rendered', 'Sem Título'))

                        noticias_coletadas.append({
                            'campus': unidade['id'],
                            'titulo': titulo_limpo,
                            'link': post.get('link', ''),
                            'data': data_limpa
                        })
                    
                    sucesso_na_unidade = True
                    print(f"   ✓ {unidade['id']} - Página {pagina} coletada com sucesso!")
                    pagina += 1
                    
                except Exception as e:
                    print(f"   X Erro na página {pagina} de {unidade['id']}: {e}")
                    break # Tenta o próximo fallback ou vai para o próximo campus

    return pd.DataFrame(noticias_coletadas)

# ==========================================
# 3. FUNÇÃO DE LIMPEZA E SALVAMENTO
# ==========================================
def limpar_e_salvar_dados(df_novo):
    if df_novo.empty:
        print("Nenhum dado retornado pelas APIs.")
        return

    df_novo = df_novo.dropna(subset=['data'])
    os.makedirs(os.path.dirname(ARQUIVO_CSV), exist_ok=True)

    if os.path.exists(ARQUIVO_CSV):
        print("Sincronizando e atualizando o histórico...")
        df_existente = pd.read_csv(ARQUIVO_CSV)
        df_final = pd.concat([df_existente, df_novo], ignore_index=True)
        # O keep='first' aqui garante que não duplicaremos
        df_final = df_final.drop_duplicates(subset=['link'], keep='last')
    else:
        print("Iniciando novo banco de dados histórico...")
        df_final = df_novo

    df_final = df_final.sort_values(by='data', ascending=False)
    df_final.to_csv(ARQUIVO_CSV, index=False, encoding='utf-8')
    print(f"Sucesso! CSV Atualizado. Total de registros globais: {len(df_final)}")

# ==========================================
# 4. EXECUÇÃO
# ==========================================
if __name__ == "__main__":
    print("Iniciando Radar de Notícias DICOM v1.3.0...")
    df_dados = extrair_noticias()
    limpar_e_salvar_dados(df_dados)
    print("Processo v1.3.0 finalizado.")
