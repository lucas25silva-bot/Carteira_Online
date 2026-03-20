import pandas as pd
import yfinance as yf
import numpy as np
import streamlit as st
import os

MAPA_SETORES_PT = {
    'Financial Services': 'Financeiro', 'Healthcare': 'Saúde', 'Technology': 'Tecnologia',
    'Industrials': 'Bens Industriais', 'Consumer Cyclical': 'Consumo Cíclico',
    'Consumer Defensive': 'Consumo Não Cíclico', 'Basic Materials': 'Materiais Básicos / Siderurgia',
    'Energy': 'Petróleo e Gás', 'Utilities': 'Energia Elétrica', 'Real Estate': 'Imobiliário',
    'Communication Services': 'Comunicações'
}

MAPA_B3_SETOR = {
    'ITSA4': 'Financeiro', 'ITSA3': 'Financeiro', 'ITUB4': 'Financeiro', 'ITUB3': 'Financeiro',
    'BBDC4': 'Financeiro', 'BBDC3': 'Financeiro', 'BBAS3': 'Financeiro', 'B3SA3': 'Financeiro',
    'BPAC11': 'Financeiro', 'SANB11': 'Financeiro', 'BBSE3': 'Financeiro', 'CXSE3': 'Financeiro',
    'PSSA3': 'Financeiro', 'IRBR3': 'Financeiro', 'BRSR6': 'Financeiro', 'ABCB4': 'Financeiro',
    'ELET3': 'Energia Elétrica', 'ELET6': 'Energia Elétrica', 'EQTL3': 'Energia Elétrica',
    'CPLE6': 'Energia Elétrica', 'CMIG4': 'Energia Elétrica', 'ENGI11': 'Energia Elétrica',
    'TAEE11': 'Energia Elétrica', 'TRPL4': 'Energia Elétrica', 'ISAE4': 'Energia Elétrica',
    'ALUP11': 'Energia Elétrica', 'EGIE3': 'Energia Elétrica', 'NEOE3': 'Energia Elétrica',
    'AURE3': 'Energia Elétrica', 'SBSP3': 'Saneamento', 'CSMG3': 'Saneamento', 'SAPR11': 'Saneamento',
    'SAPR4': 'Saneamento', 'PETR4': 'Petróleo e Gás', 'PETR3': 'Petróleo e Gás', 'PRIO3': 'Petróleo e Gás',
    'BRAV3': 'Petróleo e Gás', 'RECV3': 'Petróleo e Gás', 'ENAT3': 'Petróleo e Gás',
    'CSAN3': 'Petróleo e Gás', 'UGPA3': 'Petróleo e Gás', 'VBBR3': 'Petróleo e Gás',
    'VALE3': 'Materiais Básicos / Siderurgia', 'SUZB3': 'Materiais Básicos / Siderurgia',
    'KLBN11': 'Materiais Básicos / Siderurgia', 'CSNA3': 'Materiais Básicos / Siderurgia',
    'GGBR4': 'Materiais Básicos / Siderurgia', 'GOAU4': 'Materiais Básicos / Siderurgia',
    'USIM5': 'Materiais Básicos / Siderurgia', 'BRAP4': 'Materiais Básicos / Siderurgia',
    'CMIN3': 'Materiais Básicos / Siderurgia', 'CBAV3': 'Materiais Básicos / Siderurgia',
    'DXCO3': 'Materiais Básicos / Siderurgia', 'WEGE3': 'Bens Industriais', 'EMBR3': 'Bens Industriais',
    'CCRO3': 'Bens Industriais', 'RAIL3': 'Bens Industriais', 'AZUL4': 'Bens Industriais',
    'GOLL4': 'Bens Industriais', 'STBP3': 'Bens Industriais', 'POMO4': 'Bens Industriais',
    'TUPY3': 'Bens Industriais', 'LREN3': 'Consumo Cíclico', 'MGLU3': 'Consumo Cíclico',
    'ARZZ3': 'Consumo Cíclico', 'ALOS3': 'Consumo Cíclico', 'PETZ3': 'Consumo Cíclico',
    'SOMA3': 'Consumo Cíclico', 'CEAB3': 'Consumo Cíclico', 'GUAR3': 'Consumo Cíclico',
    'CVCB3': 'Consumo Cíclico', 'COGN3': 'Consumo Cíclico', 'YDUQ3': 'Consumo Cíclico',
    'RENT3': 'Consumo Cíclico', 'MOVI3': 'Consumo Cíclico', 'VAMO3': 'Consumo Cíclico',
    'SMFT3': 'Consumo Cíclico', 'VIVA3': 'Consumo Cíclico', 'ABEV3': 'Consumo Não Cíclico',
    'JBSS3': 'Consumo Não Cíclico', 'BRFS3': 'Consumo Não Cíclico', 'CRFB3': 'Consumo Não Cíclico',
    'ASAI3': 'Consumo Não Cíclico', 'SMTO3': 'Consumo Não Cíclico', 'SLCE3': 'Consumo Não Cíclico',
    'MRFG3': 'Consumo Não Cíclico', 'BEEF3': 'Consumo Não Cíclico', 'PCAR3': 'Consumo Não Cíclico',
    'CAML3': 'Consumo Não Cíclico', 'RADL3': 'Saúde', 'RDOR3': 'Saúde', 'HAPV3': 'Saúde',
    'FLRY3': 'Saúde', 'MATD3': 'Saúde', 'QUAL3': 'Saúde', 'BLAU3': 'Saúde', 'VVEO3': 'Saúde',
    'PNVL3': 'Saúde', 'TOTS3': 'Tecnologia', 'LWSA3': 'Tecnologia', 'VIVT3': 'Comunicações',
    'TIMS3': 'Comunicações', 'MULT3': 'Imobiliário', 'IGTI11': 'Imobiliário', 'CYRE3': 'Imobiliário',
    'EZTC3': 'Imobiliário', 'MRVE3': 'Imobiliário', 'DIRR3': 'Imobiliário', 'JHSF3': 'Imobiliário',
    'HBOR3': 'Imobiliário'
}

MAPA_BDR_BASE = {
    'AAPL34': 'AAPL', 'MSFT34': 'MSFT', 'GOGL34': 'GOOGL',
    'NVDC34': 'NVDA', 'AMZO34': 'AMZN', 'META34': 'META', 'TSLA34': 'TSLA'
}

def identificar_tipo_ativo(ticker):
    ticker = str(ticker).upper()
    if ticker.endswith('33') or ticker.endswith('34'): return 'BDR'
    if ticker.endswith('11'): return 'UNIT'
    return 'Ação'

def buscar_dados_score(ticker):
    try:
        yf_ticker = yf.Ticker(f"{ticker}.SA")
        info = yf_ticker.info
        
        setor = "Outros"
        ticker_str = str(ticker).upper()
        if ticker_str in MAPA_B3_SETOR:
            setor = MAPA_B3_SETOR[ticker_str]
        elif ticker_str[-2:] in ['33', '34', '35', '39']:
            setor = "Exterior (BDR)"
        elif ticker_str in ['BOVA11', 'IVVB11', 'SMAL11', 'HASH11', 'NASD11']:
            setor = "ETFs"
        elif ticker_str.endswith('11') and ticker_str not in ['BPAC11', 'SANB11', 'TAEE11', 'ALUP11', 'ENGI11', 'SAPR11', 'KLBN11', 'IGTI11']:
            setor = "Fundos Imobiliários (FII)"
        else:
            setor_eng = info.get('sector')
            if setor_eng: 
                setor = MAPA_SETORES_PT.get(setor_eng, setor_eng)
                
        tipo = identificar_tipo_ativo(ticker)
        pvp = None
        if tipo == 'BDR':
            ticker_base = MAPA_BDR_BASE.get(ticker.upper())
            if ticker_base:
                try:
                    info_base = yf.Ticker(ticker_base).info
                    pvp = info_base.get('priceToBook')
                except: pass
        else:
            pvp = info.get("priceToBook")

        pl = info.get("trailingPE")
        roe = info.get("returnOnEquity")
        roa = info.get("returnOnAssets")
        dy = info.get("dividendYield")
        m_ebit = info.get("operatingMargins")
        m_liq = info.get("profitMargins")
        
        total_debt = info.get("totalDebt")
        cash = info.get("totalCash")
        ebitda = info.get("ebitda")
        div_liq_ebitda = None
        if total_debt and ebitda and ebitda != 0:
            div_liq_ebitda = (total_debt - (cash or 0)) / ebitda

        return {
            "Ativo": ticker,
            "Setor": setor,
            "P/L": float(pl) if pl is not None else np.nan,
            "P/VP": float(pvp) if pvp is not None else np.nan,
            "DY (%)": float(dy) if dy is not None else np.nan,
            "D.L./EB": float(div_liq_ebitda) if div_liq_ebitda is not None else np.nan,
            "M.EBIT (%)": float(m_ebit * 100) if m_ebit is not None else np.nan,
            "M.Líq (%)": float(m_liq * 100) if m_liq is not None else np.nan,
            "ROA (%)": float(roa * 100) if roa is not None else np.nan,
            "ROE (%)": float(roe * 100) if roe is not None else np.nan
        }
    except Exception:
        return {
            "Ativo": ticker, "Setor": "Outros", "P/L": np.nan, "P/VP": np.nan, 
            "DY (%)": np.nan, "D.L./EB": np.nan, "M.EBIT (%)": np.nan, 
            "M.Líq (%)": np.nan, "ROA (%)": np.nan, "ROE (%)": np.nan
        }

def calcular_score_por_setor(df):
    d = df.copy()
    
    d['PL_pos'] = d['P/L'].where(d['P/L'] > 0, np.inf)
    d['PVP_pos'] = d['P/VP'].where(d['P/VP'] > 0, np.inf)
    d['DL_EB_pos'] = d['D.L./EB'].where(d['D.L./EB'] > 0, np.inf)
    
    # Ranks (0 a 10) agrupados pelo setor
    rank_roe = d.groupby('Setor')['ROE (%)'].rank(pct=True, ascending=True) * 10
    rank_roa = d.groupby('Setor')['ROA (%)'].rank(pct=True, ascending=True) * 10
    rank_dy = d.groupby('Setor')['DY (%)'].rank(pct=True, ascending=True) * 10
    rank_mebit = d.groupby('Setor')['M.EBIT (%)'].rank(pct=True, ascending=True) * 10
    rank_mliq = d.groupby('Setor')['M.Líq (%)'].rank(pct=True, ascending=True) * 10
    
    rank_pl = d.groupby('Setor')['PL_pos'].rank(pct=True, ascending=False) * 10
    rank_pvp = d.groupby('Setor')['PVP_pos'].rank(pct=True, ascending=False) * 10
    rank_dleb = d.groupby('Setor')['DL_EB_pos'].rank(pct=True, ascending=False) * 10

    # PESOS DOS MÚLTIPLOS
    PESOS_MULTIPLOS = {
        'P/L': 20,       
        'P/VP': 10,      
        'DY': 30,        
        'D.L./EB': 5,   
        'M.EBIT': 10,    
        'M.Líq': 5,     
        'ROA': 10,       
        'ROE': 10        
    }
    
    soma_pesos = sum(PESOS_MULTIPLOS.values())
    
    d['Score Múltiplo'] = (
        (rank_pl.fillna(0) * PESOS_MULTIPLOS['P/L']) +
        (rank_pvp.fillna(0) * PESOS_MULTIPLOS['P/VP']) +
        (rank_dy.fillna(0) * PESOS_MULTIPLOS['DY']) +
        (rank_dleb.fillna(0) * PESOS_MULTIPLOS['D.L./EB']) +
        (rank_mebit.fillna(0) * PESOS_MULTIPLOS['M.EBIT']) +
        (rank_mliq.fillna(0) * PESOS_MULTIPLOS['M.Líq']) +
        (rank_roa.fillna(0) * PESOS_MULTIPLOS['ROA']) +
        (rank_roe.fillna(0) * PESOS_MULTIPLOS['ROE'])
    ) / soma_pesos
    
    return d.drop(columns=['PL_pos', 'PVP_pos', 'DL_EB_pos'])

# ==========================================
# NOVO: Função protegida pela Memória Cache
# ==========================================
@st.cache_data(show_spinner=False, ttl=3600)
def carregar_dados_em_cache(tickers_carteira_tuple, arquivo_ibov):
    todos_tickers = set(tickers_carteira_tuple)
    
    if arquivo_ibov and os.path.exists(arquivo_ibov):
        try:
            try:
                df_ibov = pd.read_csv(arquivo_ibov, sep=";", encoding="latin1", skiprows=1)
                if len(df_ibov.columns) < 2:
                    df_ibov = pd.read_csv(arquivo_ibov, sep=";", encoding="latin1")
            except:
                df_ibov = pd.read_csv(arquivo_ibov, sep=";", encoding="latin1")
                
            col_ativo = [c for c in df_ibov.columns if 'ativo' in c.lower() or 'código' in c.lower()]
            if col_ativo:
                ativos_ibov = df_ibov[col_ativo[0]].dropna().astype(str).tolist()
                todos_tickers.update(ativos_ibov)
        except: pass
        
    dados = []
    for t in list(todos_tickers):
        dados.append(buscar_dados_score(t))
        
    df_bruto = pd.DataFrame(dados)
    df_final = calcular_score_por_setor(df_bruto)
    df_final = df_final.sort_values(by=["Setor", "Score Múltiplo"], ascending=[True, False])
    
    return df_final


def plotar_tabela_score(posicao, arquivo_ibov):
    st.subheader("Tabela de Score Fundamentalista (Por Setor)")
    
    tickers_carteira = posicao["Ticker"].dropna().unique().tolist()
    
    with st.spinner("Analisando múltiplos (Isso pode levar 1 minuto na primeira vez)..."):
        # Chama a nova função que guarda os dados na memória (usamos tuple para funcionar o cache)
        df_final = carregar_dados_em_cache(tuple(tickers_carteira), arquivo_ibov)
        
    # Filtros Lado a Lado
    col1, col2 = st.columns(2)
    opcoes_setores = sorted([s for s in df_final["Setor"].unique() if pd.notna(s)])
    opcoes_ativos = sorted([a for a in df_final["Ativo"].unique() if pd.notna(a)])

    with col1:
        filtro_setor = st.multiselect("Filtrar por Setor:", options=opcoes_setores, placeholder="Todos os setores...")
    with col2:
        filtro_ativo = st.multiselect("Filtrar por Ativo:", options=opcoes_ativos, placeholder="Todos os ativos...")

    # Aplicação dos filtros
    df_filtrado = df_final.copy()
    if filtro_setor:
        df_filtrado = df_filtrado[df_filtrado["Setor"].isin(filtro_setor)]
    if filtro_ativo:
        df_filtrado = df_filtrado[df_filtrado["Ativo"].isin(filtro_ativo)]

    def destacar_carteira(row):
        if row['Ativo'] in tickers_carteira:
            return ['background-color: #059669; color: white; font-weight: bold'] * len(row)
        return [''] * len(row)

    df_styled = df_filtrado.style.apply(destacar_carteira, axis=1)
    
    st.dataframe(
        df_styled,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Ativo": st.column_config.TextColumn("Ativo"),
            "Setor": st.column_config.TextColumn("Setor"),
            "P/L": st.column_config.NumberColumn("P/L", format="%.2f"),
            "P/VP": st.column_config.NumberColumn("P/VP", format="%.2f"),
            "DY (%)": st.column_config.NumberColumn("DY", format="%.2f%%"),
            "D.L./EB": st.column_config.NumberColumn("D.L./EB", format="%.2f"),
            "M.EBIT (%)": st.column_config.NumberColumn("M.EBIT", format="%.2f%%"),
            "M.Líq (%)": st.column_config.NumberColumn("M.Líq", format="%.2f%%"),
            "ROA (%)": st.column_config.NumberColumn("ROA", format="%.2f%%"),
            "ROE (%)": st.column_config.NumberColumn("ROE", format="%.2f%%"),
            "Score Múltiplo": st.column_config.ProgressColumn(
                "Score Final", 
                format="%.2f", 
                min_value=0, 
                max_value=10
            ),
        }
    )