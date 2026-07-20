# 📊 Painel de Performance & Radar DICOM | IF Baiano

Aplicação web e dashboard analítico para monitoramento e acompanhamento em tempo real das notícias e publicações oficiais de todos os campi e unidades da reitoria do **IF Baiano** (Diretoria de Comunicação - DICOM).

---

## 📌 Sobre a Aplicação
O sistema realiza o escaneamento automatizado das APIs da rede interna do IF Baiano (portais institucionais WordPress de cada campus) e consolida os dados em um painel interativo. Permite aos gestores de comunicação analisar o volume de publicações, estimar tempos de leitura e verificar o desempenho individual de cada unidade.

## ✨ Funcionalidades Principais
- 📡 **Robô de Coleta Incremental (*Delta Load*)**: Varre as rotas REST API de 15 unidades do IF Baiano, ignorando notícias já cadastradas e adicionando novas matérias ao banco histórico.
- 📊 **Dashboard Analítico (Streamlit & Plotly)**: Exibição de métricas gerais, ranking dos campi mais ativos e gráficos de linha do tempo de publicações.
- 🎨 **Identidade Visual Oficial**: Interface e gráficos 100% alinhados à marca institucional do IF Baiano (Verde `#3E9A2D` e Vermelho `#C80710`).
- ⏱️ **Cálculo Automático de Leitura**: Estimativa de tempo médio de leitura baseada na contagem de palavras do texto extraído das matérias.
- 📱 **Interface Paginada e Responsiva**: Tabela com ordenação da matéria mais recente para a mais antiga e busca com links diretos.

## 🛠️ Tecnologias Utilizadas
- **Frontend / Dashboard**: Streamlit, Plotly Express, HTML5, Vanilla CSS3.
- **Backend / Scraper**: Python 3.x, Pandas, Requests, BeautifulSoup4.

## 📁 Estrutura do Projeto
- `app.py`: Aplicação principal do dashboard interativo em Streamlit.
- `scraper.py`: Script de varredura automatizada das APIs do IF Baiano.
- `index.html`: Versão de pré-visualização web estática do painel.
- `data/noticias_if.csv`: Banco de dados consolidado de publicações históricas.
- `README.md`: Documentação oficial e histórico de alterações do projeto.

---

## 📜 Log de Atualizações (Changelog)

### 📅 20/07/2026 - Repaginação Premium & Bento Design (Impeccable & Brand Kit)
- 🎨 **Bento Grid & Layout Premium**: Redesenhado o painel analítico estruturando os cards em formato Bento Grid, aplicando sombras suaves e transições táteis, e eliminando o antipadrão de bordas laterais coloridas (side-stripe borders).
- 🏷️ **Favicons & Tipografia Institucional**: Adicionados favicons oficiais (`favicon-if-baiano.ico`, `favicon-if-baiano.png`) e configurada a fonte institucional `Outfit` carregada via Google Fonts.
- 🏢 **Cabeçalho Corporativo**: Substituída a logo vertical centralizada pela logo horizontal oficial (`marca-if-baiano-horizontal.png`) alinhada em um layout flexível moderno.
- 🟢 **Indicador de Atividade & Status**: Redesenhados os cards de termômetro de atividade dos campi e as tags de tipo de publicação para uma visualização limpa com dots indicativos (`🟢` e `🔴`).
- 📊 **Calibração de Gráficos**: Sincronizadas as cores internas de renderização do Chart.js com a paleta oficial de marca (Verde `#3E9A2D` e Vermelho `#C80710`).
- ⚡ **Splash Screen & Loader Animado**: Criada uma tela de carregamento (Splash Screen) em tela cheia com a marca vertical oficial (`marca-if-baiano-vertical.png`) animada com pulsação em escala, barra de progresso deslizante e efeito fade-out suave ao finalizar o carregamento dos dados.

### 📅 27/06/2026 - Recursos de Acessibilidade (A11y)
- ♿ **Acessibilidade Universal (A11y/WCAG)**: Adicionada barra flutuante de acessibilidade com **A+/A- (Ajuste de Fonte)** e modo **Alto Contraste (☯)**.

### 📅 27/06/2026 - Otimização Ponytail & Adequação Institucional IF Baiano
- 🎨 **Alinhamento da Identidade Visual**: Atualização das sequências de cores dos gráficos Plotly (`app.py`) e variáveis CSS (`index.html`) para a paleta oficial do IF Baiano (`#3E9A2D` e `#C80710`).
- ⚡ **Otimização Nativa API REST**: Refatoração do `scraper.py` para utilizar a decodificação JSON nativa (`response.json()`), eliminando bibliotecas desnecessárias de tratamento de bytes.
- ✂️ **Redução de Boilerplate**: Simplificação das operações de concatenação e desduplicação do Pandas em expressões enxutas de uma linha.
- 📚 **Atualização da Documentação**: Estruturação completa do arquivo `README.md` com changelog detalhado.
