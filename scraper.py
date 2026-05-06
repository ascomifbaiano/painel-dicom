# scraper.py - v1.14.0
import requests
import pandas as pd
import os
import html
import urllib3
import json 
import re
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
# 2. EXTRAÇÃO INCREMENTAL (DELTA LOAD)
# ==========================================
def extrair_noticias():
    noticias_coletadas = []
    
    # Carrega os links que já temos no CSV para a memória
    if os.path.exists(ARQUIVO_CSV):
        df_existente = pd.read_csv(ARQUIVO_CSV)
        links_conhecidos = set(df_existente['link'].dropna().tolist())
    else:
        links_conhecidos = set()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json'
    }

    for unidade in UNIDADES:
        print(f"Coletando: {unidade['id']}...")
        pagina = 1
        limite_atingido = False

        while not limite_atingido:
            try:
                url = f"{unidade['url']}?per_page=100&page={pagina}"
                response = requests.get(url, headers=headers, timeout=30, verify=False)
                
                if response.status_code != 200:
                    break
                    
                raw_data = response.content.decode('utf-8-sig')
                posts = json.loads(raw_data)
                
                if not posts or not isinstance(posts, list):
                    break 

                for post in posts:
                    link_post = post.get('link', '')
                    
                    # A MÁGICA INCREMENTAL: Se o link já existe no CSV, para a busca imediatamente.
                    if link_post in links_conhecidos:
                        print(f"   ✓ Ponto de sincronização alcançado. Notícias antigas ignoradas.")
                        limite_atingido = True
                        break
                        
                    data_bruta = post.get('date', '')
                    data_limpa = data_bruta.split('T')[0]
                    hora_limpa = data_bruta.split('T')[1][:5] if 'T' in data_bruta else '12:00'
                    
                    titulo_limpo = html.unescape(post.get('title', {}).get('rendered', 'Sem Título'))
                    
                    conteudo_html = post.get('content', {}).get('rendered', '')
                    texto_limpo = re.sub(r'<[^>]+>', ' ', conteudo_html)
                    qtd_palavras = len(texto_limpo.split())
                    tempo_leitura = max(1, round(qtd_palavras / 250))

                    noticias_coletadas.append({
                        'campus': unidade['id'],
                        'titulo': titulo_limpo,
                        'link': link_post,
                        'data': data_limpa,
                        'hora': hora_limpa,
                        'tempo_leitura': tempo_leitura
                    })
                
                if not limite_atingido:
                    print(f"   + Página {pagina} mapeada com novas publicações.")
                    pagina += 1
                    
            except json.JSONDecodeError as e:
                print(f"   X Falha ao decodificar JSON em {unidade['id']}: {e}")
                break
            except Exception as e:
                print(f"   X Falha na rota de {unidade['id']}: {e}")
                break 

        if len(noticias_coletadas) > 0:
            print(f"✅ Atualização concluída para {unidade['id']}.")
        else:
            print(f"⚡ Nenhuma notícia nova em {unidade['id']}.")

    return pd.DataFrame(noticias_coletadas)

# ==========================================
# 3. SALVAMENTO ESTRUTURADO
# ==========================================
def limpar_e_salvar_dados(df_novo):
    if df_novo.empty:
        print("Nenhum dado novo retornado pelas APIs hoje. Sistema atualizado.")
        return

    df_novo = df_novo.dropna(subset=['data'])
    os.makedirs(os.path.dirname(ARQUIVO_CSV), exist_ok=True)

    if os.path.exists(ARQUIVO_CSV):
        print(f"Adicionando {len(df_novo)} novas publicações ao banco histórico...")
        df_existente = pd.read_csv(ARQUIVO_CSV)
        # Coloca as novas em cima das velhas e remove duplicatas por segurança
        df_final = pd.concat([df_novo, df_existente], ignore_index=True)
        df_final = df_final.drop_duplicates(subset=['link'], keep='first')
    else:
        print("Criando primeiro banco de dados...")
        df_final = df_novo

    df_final = df_final.sort_values(by=['data', 'hora'], ascending=[False, False])
    df_final.to_csv(ARQUIVO_CSV, index=False, encoding='utf-8')
    print(f"Sucesso! Total consolidado: {len(df_final)} notícias no acervo geral.")

# ==========================================
# 4. EXECUÇÃO
# ==========================================
if __name__ == "__main__":
    print("Iniciando Painel DICOM v1.14.0 (Incremental Sync)...")
    df_dados = extrair_noticias()
    limpar_e_salvar_dados(df_dados)
    print("Processo v1.14.0 finalizado.")
