import pandas as pd
import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import re

# ========================================================
# DICIONÁRIO "DE/PARA": TICKER -> NOME NO RANKING MERCO
# ========================================================
# Esse mapa traduz as 4 letras iniciais do ticker para o nome comercial da empresa
MAPA_TICKER_NOME = {
    'ITUB': 'Itaú', 'BBDC': 'Bradesco', 'BBAS': 'Banco do Brasil', 'SANB': 'Santander', 'BPAC': 'BTG',
    'ABEV': 'Ambev', 'NTCO': 'Natura', 'WEGE': 'Weg', 'MGLU': 'Magazine Luiza', 
    'PETR': 'Petrobras', 'VALE': 'Vale', 'SUZB': 'Suzano', 'KLBN': 'Klabin', 
    'LREN': 'Renner', 'RADL': 'Raia', 'RDOR': 'Rede D', 'HAPV': 'Hapvida', 'FLRY': 'Fleury',
    'VIVT': 'Vivo', 'TIMS': 'TIM', 'B3SA': 'B3', 'JBSS': 'JBS', 'BRFS': 'BRF', 'MRFG': 'Marfrig',
    'CSNA': 'CSN', 'GGBR': 'Gerdau', 'USIM': 'Usiminas', 'RENT': 'Localiza', 
    'CCRO': 'CCR', 'RAIL': 'Rumo', 'AZUL': 'Azul', 'GOLL': 'Gol', 'EMBR': 'Embraer',
    'ELET': 'Eletrobras', 'CMIG': 'Cemig', 'SBSP': 'Sabesp', 'CPLE': 'Copel', 'EQTL': 'Equatorial',
    'ENEV': 'Eneva', 'EGIE': 'Engie', 'TOTS': 'Totvs', 'MULT': 'Multiplan', 'IGTI': 'Iguatemi',
    'CYRE': 'Cyrela', 'MRVE': 'MRV', 'EZTC': 'Eztec', 'ASAI': 'Assaí', 'CRFB': 'Carrefour',
    'PCAR': 'Pão de Açúcar', 'YDUQ': 'Yduqs', 'COGN': 'Cogna', 'CSAN': 'Cosan', 
    'UGPA': 'Ultrapar', 'VBBR': 'Vibra', 'PRIO': 'Prio', 'ENAT': 'Enauta',
    'MELI': 'Mercado Livre', 'AMZO': 'Amazon', 'GOGL': 'Google', 'MSFT': 'Microsoft', 'AAPL': 'Apple'
}

# ========================================================
# FUNÇÃO DE RASPAGEM (WEB SCRAPING) COM BUSCA RETROATIVA
# ========================================================
@st.cache_data(show_spinner=False, ttl=86400) # Atualiza no máximo 1x por dia para não sobrecarregar o site
def buscar_ranking_merco():
    ano_atual = datetime.now().year
    anos_para_tentar = [ano_atual, ano_atual - 1, ano_atual - 2, 2024]
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    for ano in anos_para_tentar:
        url = f"https://www.merco.info/br/ranking-merco-responsabilidad-gobierno-corporativo?edicion={ano}"
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, 'html.parser')
                
                # Procura a tabela de ranking no HTML do Merco
                tabelas = soup.find_all('table')
                if tabelas:
                    df = pd.read_html(str(tabelas[0]))[0]
                    # Limpa os nomes das colunas baseando-se no padrão deles
                    if len(df.columns) >= 3:
                        df.columns = ['Posição', 'Empresa', 'Pontuação'] + list(df.columns[3:])
                        df = df[['Posição', 'Empresa', 'Pontuação']].dropna(subset=['Empresa'])
                        
                        # Converte pontuação para número caso venha como texto
                        df['Pontuação'] = pd.to_numeric(df['Pontuação'], errors='coerce')
                        df['Posição'] = pd.to_numeric(df['Posição'], errors='coerce')
                        return df
        except Exception:
            continue
            
    # Se falhar tudo (ex: site fora do ar), retorna um dataframe vazio com a estrutura correta
    return pd.DataFrame(columns=['Posição', 'Empresa', 'Pontuação'])

def extrair_base_ticker(ticker):
    # Pega apenas as letras do ticker (ex: ITUB4 -> ITUB)
    return re.sub(r'[0-9]+', '', str(ticker)).upper()

@st.cache_data(show_spinner=False, ttl=3600)
def carregar_dados_esg(tickers_carteira_tuple, arquivo_ibov):
    todos_tickers = set(tickers_carteira_tuple)
    
    # Adiciona os ativos do IBOV para comparação
    if arquivo_ibov and os.path.exists(arquivo_ibov):
        try:
            df_ibov = pd.read_csv(arquivo_ibov, sep=";", encoding="latin1")
            col_ativo = [c for c in df_ibov.columns if 'ativo' in c.lower() or 'código' in c.lower()]
            if col_ativo:
                ativos_ibov = df_ibov[col_ativo[0]].dropna().astype(str).tolist()
                todos_tickers.update(ativos_ibov)
        except: pass
        
    df_merco = buscar_ranking_merco()
    dados = []
    
    for ticker in list(todos_tickers):
        base_ticker = extrair_base_ticker(ticker)
        nome_busca = MAPA_TICKER_NOME.get(base_ticker, str(ticker))
        
        posicao_merco = np.nan
        pontuacao = np.nan
        empresa_merco = "-"
        
        # Faz a busca "Fuzzy": Verifica se a palavra traduzida (ex: 'Itaú') está no nome que veio do site
        if not df_merco.empty:
            match = df_merco[df_merco['Empresa'].str.contains(nome_busca, case=False, na=False)]
            if not match.empty:
                posicao_merco = match.iloc[0]['Posição']
                pontuacao = match.iloc[0]['Pontuação']
                empresa_merco = match.iloc[0]['Empresa']
                
        # CÁLCULO DA NOTA ESG (0 a 10)
        nota_esg = 0
        if pd.notna(pontuacao) and pontuacao > 0:
            nota_esg = (pontuacao / 10000) * 10
            nota_esg = min(nota_esg, 10.0) # Garante que não passe de 10
        elif pd.notna(posicao_merco) and posicao_merco > 0:
            nota_esg = max(10 - ((posicao_merco - 1) * 0.1), 0.1) # Vai caindo de 0.1 em 0.1 a cada posição

        dados.append({
            'Ativo': ticker,
            'Nome Merco': empresa_merco,
            'Posição Ranking': posicao_merco,
            'Pontuação ESG': pontuacao,
            'Nota ESG': nota_esg
        })
        
    df_final = pd.DataFrame(dados)
    
    # Ordena para colocar quem tem nota primeiro
    df_final['is_ibov'] = df_final['Ativo'] == 'IBOVESPA'
    df_final = df_final.sort_values(by=['Nota ESG', 'Ativo'], ascending=[False, True]).drop(columns=['is_ibov'], errors='ignore')
    
    return df_final


def plotar_tabela_esg(posicao, arquivo_ibov):
    st.subheader("🌱 Tabela de Governança e Sustentabilidade (Ranking Merco ESG)")
    
    tickers_carteira = posicao["Ticker"].dropna().unique().tolist()
    
    with st.spinner("Conectando ao banco de dados Merco e traduzindo ativos..."):
        df_final = carregar_dados_esg(tuple(tickers_carteira), arquivo_ibov)
        
    # Filtro para Ativos
    opcoes_ativos = sorted([a for a in df_final["Ativo"].unique() if pd.notna(a)])
    filtro_ativo = st.multiselect("Filtrar ESG por Ativo:", options=opcoes_ativos, placeholder="Todos os ativos...")

    if filtro_ativo:
        df_filtrado = df_final[df_final["Ativo"].isin(filtro_ativo)].copy()
    else:
        df_filtrado = df_final.copy()

    def aplicar_estilos(row):
        estilos = [''] * len(row)
        is_carteira = row['Ativo'] in tickers_carteira
        
        for i in range(len(row)):
            if is_carteira:
                estilos[i] = 'background-color: #059669; color: white; font-weight: bold'
        return estilos

    # Trata visualmente quem não está no ranking
    def formatar_posicao(val):
        if pd.isna(val) or val == 0: return "Não Rankeado"
        return f"{int(val)}º Lugar"

    def formatar_pontuacao(val):
        if pd.isna(val) or val == 0: return "-"
        return f"{int(val)} pts"

    df_styled = df_filtrado.style.apply(aplicar_estilos, axis=1).format({
        'Posição Ranking': formatar_posicao,
        'Pontuação ESG': formatar_pontuacao
    })
    
    st.dataframe(
        df_styled,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Ativo": st.column_config.TextColumn("Ativo (B3)"),
            "Nome Merco": st.column_config.TextColumn("Nome Encontrado no Ranking"),
            "Posição Ranking": st.column_config.TextColumn("Posição Nacional"),
            "Pontuação ESG": st.column_config.TextColumn("Pontuação Merco"),
            "Nota ESG": st.column_config.ProgressColumn(
                "Nota Governança (0 a 10)", 
                format="%.2f", 
                min_value=0, 
                max_value=10
            )
        }
    )
    
    # Retorna o Dataframe para uso futuro no Ranking Unificado
    return df_final