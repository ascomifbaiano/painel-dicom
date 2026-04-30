# Painel DICOM | IF Baiano v1.14.0

Sistema de Business Intelligence (BI) e Monitoramento de Comunicação Estratégica para o IF Baiano.

##  Funcionalidades
- **Scraping Multi-unidade:** Coleta automática das 15 unidades do IF Baiano via API REST WordPress.
- **Dashboard Analítico:** Visualização de volume, evolução temporal, classificação de conteúdo e produtividade.
- **Termômetro de Atividade:** Monitoramento de dias sem publicações por unidade.
- **Exportação PDF:** Geração de relatórios de métricas com um clique.
- **Automação GitHub Actions:** Atualização de dados a cada 30 minutos.

##  Tecnologias
- **Backend:** Python (Pandas, Requests)
- **Frontend:** HTML5, CSS3 (Plus Jakarta Sans), JavaScript (Vanilla)
- **Gráficos:** Chart.js
- **Automação:** GitHub Actions

##  Como usar
1. O painel principal pode ser acessado abrindo o arquivo `index.html`.
2. Para executar o scraper manualmente: `python scraper.py`
3. (Opcional) Para o dashboard Streamlit: `streamlit run app.py`

---
*Powered by DICOM - Diretoria de Comunicação do IF Baiano*
