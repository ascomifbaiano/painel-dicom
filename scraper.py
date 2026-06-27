import os
import re
import html
import requests
import urllib3
import pandas as pd

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

def extrair_noticias():
    noticias_coletadas = []
    links_conhecidos = set(pd.read_csv(ARQUIVO_CSV)['link'].dropna().tolist()) if os.path.exists(ARQUIVO_CSV) else set()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}

    for unidade in UNIDADES:
        print(f"Coletando Rede Interna: {unidade['id']}...")
        pagina = 1
        limite_atingido = False

        while not limite_atingido:
            try:
                url = f"{unidade['url']}?per_page=100&page={pagina}"
                response = requests.get(url, headers=headers, timeout=30, verify=False)
                if response.status_code != 200: break
                    
                posts = response.json()
                if not posts or not isinstance(posts, list): break 

                for post in posts:
                    link_post = post.get('link', '')
                    if link_post in links_conhecidos:
                        print("   ✓ Sincronizado. Notícias antigas ignoradas.")
                        limite_atingido = True
                        break
                        
                    data_bruta = post.get('date', '')
                    data_limpa = data_bruta.split('T')[0]
                    hora_limpa = data_bruta.split('T')[1][:5] if 'T' in data_bruta else '12:00'
                    titulo_limpo = html.unescape(post.get('title', {}).get('rendered', 'Sem Título'))
                    
                    conteudo_html = post.get('content', {}).get('rendered', '')
                    qtd_palavras = len(re.sub(r'<[^>]+>', ' ', conteudo_html).split())
                    tempo_leitura = max(1, round(qtd_palavras / 250))

                    noticias_coletadas.append({
                        'campus': unidade['id'], 'titulo': titulo_limpo, 'link': link_post,
                        'data': data_limpa, 'hora': hora_limpa, 'tempo_leitura': tempo_leitura
                    })
                
                if not limite_atingido: pagina += 1
            except Exception as e:
                print(f"   X Falha na rota de {unidade['id']}: {e}")
                break 

    return pd.DataFrame(noticias_coletadas)

def limpar_e_salvar_dados(df_novo):
    if df_novo.empty:
        print("Nenhum dado novo retornado pelas APIs hoje. Sistema atualizado.")
        return

    df_novo = df_novo.dropna(subset=['data'])
    os.makedirs(os.path.dirname(ARQUIVO_CSV), exist_ok=True)

    if os.path.exists(ARQUIVO_CSV):
        print(f"Adicionando {len(df_novo)} novas publicações ao banco histórico...")
        df_existente = pd.read_csv(ARQUIVO_CSV)
        df_final = pd.concat([df_novo, df_existente], ignore_index=True).drop_duplicates(subset=['link'], keep='first')
    else:
        print("Criando primeiro banco de dados...")
        df_final = df_novo

    df_final.sort_values(by=['data', 'hora'], ascending=[False, False]).to_csv(ARQUIVO_CSV, index=False, encoding='utf-8')
    print(f"Sucesso! Total consolidado: {len(df_final)} notícias na rede interna.")

if __name__ == "__main__":
    print("Iniciando Painel DICOM (Portais Internos - Ponytail Mode)...")
    limpar_e_salvar_dados(extrair_noticias())
    print("Processo finalizado.")
