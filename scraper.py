# scraper.py - v1.11.0
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
# 1. CONFIGURAÇÕES GERAIS E JANELA DE TEMPO
# ==========================================
ARQUIVO_CSV = 'data/noticias_if.csv'

ANO_ATUAL = datetime.now().year
ANO_LIMITE = ANO_ATUAL - 2
DATA_LIMITE = f"{ANO_LIMITE}-01-01"

print(f"-> Ano Atual: {ANO_ATUAL} | Limite de Retenção: {DATA_LIMITE}")

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
# 2. EXTRAÇÃO DE DADOS PROFUNDOS
# ==========================================
def extrair_noticias():
    noticias_coletadas = []
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
                    print(f"   X Erro de Servidor: Status {response.status_code}")
                    break
                    
                raw_data = response.content.decode('utf-8-sig')
                posts = json.loads(raw_data)
                
                if not posts or not isinstance(posts, list):
                    break 

                for post in posts:
                    data_bruta = post.get('date', '')
                    data_limpa = data_bruta.split('T')[0]
                    hora_limpa = data_bruta.split('T')[1][:5] if 'T' in data_bruta else '12:00'
                    
                    if data_limpa < DATA_LIMITE:
                        limite_atingido = True
                        break

                    titulo_limpo = html.unescape(post.get('title', {}).get('rendered', 'Sem Título'))
                    
                    conteudo_html = post.get('content', {}).get('rendered', '')
                    texto_limpo = re.sub(r'<[^>]+>', ' ', conteudo_html)
                    qtd_palavras = len(texto_limpo.split())
                    tempo_leitura = max(1, round(qtd_palavras / 250))

                    noticias_coletadas.append({
                        'campus': unidade['id'],
                        'titulo': titulo_limpo,
                        'link': post.get('link', ''),
                        'data': data_limpa,
                        'hora': hora_limpa,
                        'tempo_leitura': tempo_leitura
                    })
                
                if not limite_atingido:
                    print(f"   ✓ Página {pagina} processada.")
                    pagina += 1
                    
            except json.JSONDecodeError as e:
                print(f"   X Falha ao decodificar JSON em {unidade['id']}: {e}")
                break
            except Exception as e:
                print(f"   X Falha na rota de {unidade['id']}: {e}")
                break 

        if len(noticias_coletadas) > 0:
            print(f"✅ Fim da varredura para {unidade['id']}.")

    return pd.DataFrame(noticias_coletadas)

# ==========================================
# 3. SALVAMENTO E PURGA
# ==========================================
def limpar_e_salvar_dados(df_novo):
    if df_novo.empty:
        print("Nenhum dado novo retornado pelas APIs hoje.")
        df_novo = pd.DataFrame(columns=['campus', 'titulo', 'link', 'data', 'hora', 'tempo_leitura']) 

    df_novo = df_novo.dropna(subset=['data'])
    os.makedirs(os.path.dirname(ARQUIVO_CSV), exist_ok=True)

    if os.path.exists(ARQUIVO_CSV):
        print("Atualizando banco de dados histórico...")
        df_existente = pd.read_csv(ARQUIVO_CSV)
        df_final = pd.concat([df_existente, df_novo], ignore_index=True)
        df_final = df_final.drop_duplicates(subset=['link'], keep='last')
    else:
        print("Criando primeiro banco de dados...")
        df_final = df_novo

    total_antes = len(df_final)
    df_final = df_final[df_final['data'] >= DATA_LIMITE]
    total_removido = total_antes - len(df_final)
    
    if total_removido > 0:
        print(f"🧹 Purga Automática: {total_removido} notícias anteriores a {DATA_LIMITE} apagadas.")

    df_final = df_final.sort_values(by=['data', 'hora'], ascending=[False, False])
    df_final.to_csv(ARQUIVO_CSV, index=False, encoding='utf-8')
    print(f"Sucesso! Total consolidado: {len(df_final)} notícias retidas.")

# ==========================================
# 4. EXECUÇÃO
# ==========================================
if __name__ == "__main__":
    print("Iniciando Painel DICOM v1.11.0...")
    df_dados = extrair_noticias()
    limpar_e_salvar_dados(df_dados)
    print("Processo v1.11.0 finalizado.")
