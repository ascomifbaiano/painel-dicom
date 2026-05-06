# scraper.py - v1.20.0
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
# FUNÇÕES DE LIMPEZA E CLASSIFICAÇÃO (HEURÍSTICA)
# ==========================================
def padronizar_data(data_str, ano_referencia=str(datetime.now().year)):
    d_str = str(data_str).strip().lower()
    
    meses = {'janeiro':'01','fevereiro':'02','março':'03','marco':'03','abril':'04','maio':'05','junho':'06',
             'julho':'07','agosto':'08','setembro':'09','outubro':'10','novembro':'11','dezembro':'12'}
    for pt, num in meses.items():
        d_str = d_str.replace(pt, num)
        
    match = re.search(r'(\d{4})-(\d{2})-(\d{2})', d_str)
    if match: return match.group(0)

    match = re.search(r'(\d{2})[-/](\d{2})[-/](\d{2,4})', d_str)
    if match:
        d, m, y = match.groups()
        if len(y) == 2: y = '20' + y
        return f"{y}-{m.zfill(2)}-{d.zfill(2)}"

    match = re.search(r'(\d{1,2})\s+(?:de\s+)?(\d{2})\s+(?:de\s+)?(\d{4})', d_str)
    if match:
        d, m, y = match.groups()
        return f"{y}-{m.zfill(2)}-{d.zfill(2)}"

    match = re.search(r'(\d{2})[-/](\d{4})', d_str)
    if match:
        m, y = match.groups()
        return f"{y}-{m.zfill(2)}-01"

    match = re.search(r'(\d{2})[-/](\d{2})', d_str)
    if match:
        d, m = match.groups()
        return f"{ano_referencia}-{m.zfill(2)}-{d.zfill(2)}"

    return f"{ano_referencia}-01-01"

def classificar_eixo(titulo):
    t = str(titulo).lower()
    if any(w in t for w in ['sisu', 'prosel', 'vaga', 'curso', 'graduação', 'especialização', 'técnico', 'matrícula', 'ensino', 'aluno', 'estudante', 'aula']): return 'Ensino'
    if any(w in t for w in ['pesquisa', 'ciência', 'tecnologia', 'inovação', 'patente', 'cnpq', 'artigo', 'fapesb', 'científica', 'pesquisador', 'desenvolve', 'biofilme']): return 'Pesquisa'
    if any(w in t for w in ['extensão', 'comunidade', 'projeto', 'feira', 'evento', 'seminário', 'agricultura familiar', 'mulheres mil', 'oficina', 'tenda']): return 'Extensão'
    return 'Institucional'

def classificar_abrangencia(veiculo):
    v = str(veiculo).lower()
    if any(w in v for w in ['g1', 'cnn', 'r7', 'terra', 'estadao', 'msn', 'uol', 'record', 'band', 'catraca livre', 'o tempo']): return 'Nacional'
    if any(w in v for w in ['a tarde', 'correio', 'bnews', 'aratu', 'ibahia', 'tribuna da bahia', 'bahia notícias', 'farol da bahia', 'bahia.ba', 'bahia já']): return 'Regional (Bahia)'
    if any(w in v for w in ['prefeitura', 'gov.br', 'conif', 'mec', 'if baiano', 'ufba', 'uesb', 'ifba', 'adab', 'codevasf', 'embrapa']): return 'Institucional / Governamental'
    if any(w in v for w in ['concurso', 'pci', 'qconcursos', 'ache', 'direção', 'estrategia', 'educação', 'agro', 'rural', 'defesa', 'tecnologia', 'focus']): return 'Especializados (Nichos)'
    return 'Imprensa Local'

# ==========================================
# EXTRAÇÃO DE PORTAIS
# ==========================================
def extrair_noticias():
    noticias_coletadas = []
    df_existente = pd.read_csv(ARQUIVO_CSV) if os.path.exists(ARQUIVO_CSV) else pd.DataFrame()
    links_conhecidos = set(df_existente['link'].dropna().tolist()) if not df_existente.empty else set()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Accept': 'application/json'}

    for unidade in UNIDADES:
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
                    data_limpa = post.get('date', '').split('T')[0]
                    hora_limpa = post.get('date', '').split('T')[1][:5] if 'T' in post.get('date', '') else '12:00'
                    titulo_limpo = html.unescape(post.get('title', {}).get('rendered', 'Sem Título'))
                    texto_limpo = re.sub(r'<[^>]+>', ' ', post.get('content', {}).get('rendered', ''))
                    noticias_coletadas.append({'campus': unidade['id'], 'titulo': titulo_limpo, 'link': link_post, 'data': data_limpa, 'hora': hora_limpa, 'tempo_leitura': max(1, round(len(texto_limpo.split()) / 250))})
                if not limite_atingido: pagina += 1
            except Exception as e: break 
    return pd.DataFrame(noticias_coletadas)

def limpar_e_salvar_dados(df_novo):
    if df_novo.empty: return
    df_novo = df_novo.dropna(subset=['data'])
    os.makedirs(os.path.dirname(ARQUIVO_CSV), exist_ok=True)
    if os.path.exists(ARQUIVO_CSV): df_final = pd.concat([df_novo, pd.read_csv(ARQUIVO_CSV)], ignore_index=True).drop_duplicates(subset=['link'], keep='first')
    else: df_final = df_novo
    df_final.sort_values(by=['data', 'hora'], ascending=[False, False]).to_csv(ARQUIVO_CSV, index=False, encoding='utf-8')

# ==========================================
# EXTRAÇÃO DE CLIPPING (Google + Bing + Tratamento Base Manual)
# ==========================================
def processar_clipping():
    print("Processando Clipping Inteligente...")
    links_conhecidos = set()
    df_existente = pd.DataFrame()

    if os.path.exists(ARQUIVO_CLIPPING):
        try:
            df_existente = pd.read_csv(ARQUIVO_CLIPPING, on_bad_lines='skip')
            # Limpeza retroativa do arquivo manual
            if 'data' in df_existente.columns:
                df_existente['data'] = df_existente['data'].apply(lambda x: padronizar_data(x))
            if 'eixo_institucional' not in df_existente.columns:
                df_existente['eixo_institucional'] = df_existente['assunto'].apply(classificar_eixo)
            if 'abrangencia' not in df_existente.columns:
                df_existente['abrangencia'] = df_existente['veiculo'].apply(classificar_abrangencia)
            links_conhecidos = set(df_existente['link'].dropna().tolist())
        except Exception as e:
            print(f"Erro ao ler CSV atual: {e}")

    clipping_coletado = []
    fontes_pesquisa = [
        ("Google News", 'https://news.google.com/rss/search?q="IF+Baiano"&hl=pt-BR&gl=BR&ceid=BR:pt-419'),
        ("Bing News", 'https://www.bing.com/news/search?q="IF+Baiano"&format=rss')
    ]
    
    for nome_motor, url_rss in fontes_pesquisa:
        try:
            response = requests.get(url_rss, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
            root = ET.fromstring(response.content)
            for item in root.findall('./channel/item'):
                link = item.find('link').text
                if link in links_conhecidos: continue 
                
                titulo_completo = item.find('title').text or 'Sem Título'
                veiculo = html.unescape(item.find('source').text) if item.find('source') is not None and item.find('source').text else "Mídia Externa"
                
                if veiculo == "Mídia Externa" and ' - ' in titulo_completo:
                    titulo, veiculo = (html.unescape(p.strip()) for p in titulo_completo.rsplit(' - ', 1))
                else:
                    titulo = html.unescape(titulo_completo.rsplit(' - ', 1)[0] if ' - ' in titulo_completo else titulo_completo)

                data_pub = padronizar_data(item.find('pubDate').text)
                
                clipping_coletado.append({
                    'data': data_pub,
                    'assunto': titulo,
                    'veiculo': veiculo,
                    'link': link,
                    'eixo_institucional': classificar_eixo(titulo),
                    'abrangencia': classificar_abrangencia(veiculo)
                })
                links_conhecidos.add(link) 
        except Exception as e: pass

    df_novo = pd.DataFrame(clipping_coletado)
    df_final = pd.concat([df_novo, df_existente], ignore_index=True) if not df_novo.empty else df_existente
    
    if not df_final.empty:
        df_final.sort_values(by=['data'], ascending=[False]).to_csv(ARQUIVO_CLIPPING, index=False, encoding='utf-8')
        print(f"Clipping atualizado: {len(df_final)} registros. Tags e Datas padronizadas.")

if __name__ == "__main__":
    print("Iniciando Painel DICOM v1.20.0...")
    limpar_e_salvar_dados(extrair_noticias())
    processar_clipping()
    print("Sucesso!")
