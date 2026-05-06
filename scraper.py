# scraper.py - v1.18.0
import requests
import pandas as pd
import os
import html
import urllib3
import json 
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# 1. CONFIGURAÇÕES GERAIS
# ==========================================
ARQUIVO_CSV = 'data/noticias_if.csv'
ARQUIVO_CLIPPING = 'data/clipping.csv'

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
# 2. MOTOR 1: PORTAIS DO IF BAIANO
# ==========================================
def extrair_noticias():
    noticias_coletadas = []
    df_existente = pd.read_csv(ARQUIVO_CSV) if os.path.exists(ARQUIVO_CSV) else pd.DataFrame()
    links_conhecidos = set(df_existente['link'].dropna().tolist()) if not df_existente.empty else set()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept': 'application/json'
    }

    for unidade in UNIDADES:
        print(f"Coletando Rede Interna: {unidade['id']}...")
        pagina = 1
        limite_atingido = False

        while not limite_atingido:
            try:
                url = f"{unidade['url']}?per_page=100&page={pagina}"
                response = requests.get(url, headers=headers, timeout=30, verify=False)
                
                if response.status_code != 200: break
                posts = json.loads(response.content.decode('utf-8-sig'))
                if not posts or not isinstance(posts, list): break 

                for post in posts:
                    link_post = post.get('link', '')
                    if link_post in links_conhecidos:
                        limite_atingido = True
                        break
                        
                    data_bruta = post.get('date', '')
                    data_limpa = data_bruta.split('T')[0]
                    hora_limpa = data_bruta.split('T')[1][:5] if 'T' in data_bruta else '12:00'
                    titulo_limpo = html.unescape(post.get('title', {}).get('rendered', 'Sem Título'))
                    
                    conteudo_html = post.get('content', {}).get('rendered', '')
                    texto_limpo = re.sub(r'<[^>]+>', ' ', conteudo_html)
                    tempo_leitura = max(1, round(len(texto_limpo.split()) / 250))

                    noticias_coletadas.append({'campus': unidade['id'], 'titulo': titulo_limpo, 'link': link_post, 'data': data_limpa, 'hora': hora_limpa, 'tempo_leitura': tempo_leitura})
                
                if not limite_atingido: pagina += 1
            except Exception as e:
                break 

    return pd.DataFrame(noticias_coletadas)

def limpar_e_salvar_dados(df_novo):
    if df_novo.empty: return
    df_novo = df_novo.dropna(subset=['data'])
    os.makedirs(os.path.dirname(ARQUIVO_CSV), exist_ok=True)
    if os.path.exists(ARQUIVO_CSV):
        df_final = pd.concat([df_novo, pd.read_csv(ARQUIVO_CSV)], ignore_index=True).drop_duplicates(subset=['link'], keep='first')
    else:
        df_final = df_novo
    df_final.sort_values(by=['data', 'hora'], ascending=[False, False]).to_csv(ARQUIVO_CSV, index=False, encoding='utf-8')
    print(f"Rede Interna consolidada: {len(df_final)} registros.")

# ==========================================
# 3. MOTOR 2: CLIPPING CONTÍNUO (MÍDIA EXTERNA)
# ==========================================
def extrair_clipping():
    print("\nBuscando IF Baiano na Mídia Externa (Multi-Engine)...")
    clipping_coletado = []
    
    # Tratamento de erro na leitura do CSV manual do usuário (ignora linhas quebradas pelo Excel)
    if os.path.exists(ARQUIVO_CLIPPING):
        try:
            df_existente = pd.read_csv(ARQUIVO_CLIPPING, on_bad_lines='skip')
            links_conhecidos = set(df_existente['link'].dropna().tolist())
        except:
            print("Aviso: Falha ao ler clipping.csv atual. Criando nova base.")
            links_conhecidos = set()
    else:
        links_conhecidos = set()

    fontes_pesquisa = [
        ("Google News", 'https://news.google.com/rss/search?q="IF+Baiano"&hl=pt-BR&gl=BR&ceid=BR:pt-419'),
        ("Bing News", 'https://www.bing.com/news/search?q="IF+Baiano"&format=rss')
    ]
    
    for nome_motor, url_rss in fontes_pesquisa:
        print(f" -> Varrendo {nome_motor}...")
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
            response = requests.get(url_rss, headers=headers, timeout=30)
            root = ET.fromstring(response.content)
            
            for item in root.findall('./channel/item'):
                link = item.find('link').text
                
                # A MÁGICA INCREMENTAL: Se o link já está no CSV manual ou foi lido agora, pula!
                if link in links_conhecidos:
                    continue 
                    
                titulo_completo = item.find('title').text if item.find('title') is not None else 'Sem Título'
                veiculo = "Mídia Externa"
                
                source_tag = item.find('source')
                if source_tag is not None and source_tag.text:
                    veiculo = html.unescape(source_tag.text)
                    if ' - ' in titulo_completo and veiculo in titulo_completo:
                        titulo_completo = titulo_completo.rsplit(' - ', 1)[0]
                    titulo = html.unescape(titulo_completo)
                else:
                    if ' - ' in titulo_completo:
                        partes = titulo_completo.rsplit(' - ', 1)
                        titulo = html.unescape(partes[0].strip())
                        veiculo = html.unescape(partes[1].strip())
                    else:
                        titulo = html.unescape(titulo_completo)

                data_pub_rss = item.find('pubDate').text
                try:
                    data_formatada = parsedate_to_datetime(data_pub_rss).strftime('%Y-%m-%d')
                except:
                    data_formatada = datetime.now().strftime('%Y-%m-%d')

                clipping_coletado.append({
                    'data': data_formatada,
                    'assunto': titulo,
                    'veiculo': veiculo,
                    'link': link
                })
                
                links_conhecidos.add(link) 
                
        except Exception as e:
            print(f"   X Erro ao buscar no {nome_motor}: {e}")

    return pd.DataFrame(clipping_coletado)

def salvar_clipping(df_novo):
    if df_novo.empty: 
        print("Nenhuma notícia nova na mídia hoje.")
        return
        
    os.makedirs(os.path.dirname(ARQUIVO_CLIPPING), exist_ok=True)
    if os.path.exists(ARQUIVO_CLIPPING):
        print(f"Adicionando {len(df_novo)} novas publicações ao Acervo Memorial de Clipping...")
        try:
            df_existente = pd.read_csv(ARQUIVO_CLIPPING, on_bad_lines='skip')
            df_final = pd.concat([df_novo, df_existente], ignore_index=True).drop_duplicates(subset=['link'], keep='first')
        except:
            df_final = df_novo
    else:
        df_final = df_novo

    # Ordena as notícias sempre pela data mais recente
    df_final.sort_values(by=['data'], ascending=[False]).to_csv(ARQUIVO_CLIPPING, index=False, encoding='utf-8')
    print(f"Acervo de Clipping Consolidado: {len(df_final)} registros totais na base.")

# ==========================================
# 4. EXECUÇÃO DUPLA
# ==========================================
if __name__ == "__main__":
    print("Iniciando Painel DICOM v1.18.0 (Continuous Memorial)...")
    df_portais = extrair_noticias()
    limpar_e_salvar_dados(df_portais)
    
    df_midia = extrair_clipping()
    salvar_clipping(df_midia)
    
    print("Processo v1.18.0 finalizado.")
