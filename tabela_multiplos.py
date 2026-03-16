import pandas as pd
import yfinance as yf
import numpy as np
import streamlit as st
import os

MAPA_BDR_BASE = {
    'AAPL34': 'AAPL', 'MSFT34': 'MSFT', 'GOGL34': 'GOOGL',
    'NVDC34': 'NVDA', 'AMZO34': 'AMZN', 'META34': 'META', 'TSLA34': 'TSLA'
}

def identificar_tipo_ativo(ticker):
    ticker = str(ticker).upper()
    if ticker.endswith('33') or ticker.endswith('34'): return 'BDR'
    if ticker.endswith('11'): return 'UNIT'
    return 'Ação'

# ========================================================
# MAPAS DE SETORES PADRÃO DA CARTEIRA (Mesmos do Alocação)
# ========================================================
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

def buscar_multiplos(ticker):
    try:
        yf_ticker = yf.Ticker(f"{ticker}.SA")
        info = yf_ticker.info
        
        pl = info.get("trailingPE")
        pvp = None
        
        # IDENTIFICA O SETOR USANDO A LÓGICA PADRÃO DA CARTEIRA
        setor = "Outros"
        ticker_str = str(ticker).upper()
        
        if ticker_str in MAPA_B3_SETOR:
            setor = MAPA_B3_SETOR[ticker_str]
        elif ticker_str[-2:] in ['33', '34', '35', '39']:
            setor = "Exterior (BDR)"
        elif ticker_str in ['BOVA11', 'IVVB11', 'SMAL11', 'HASH11', 'NASD11', 'DIVO11', 'FIXA11', 'BINA11', 'XINA11', 'GOLD11']:
            setor = "ETFs"
        elif ticker_str.endswith('11') and ticker_str not in ['BPAC11', 'SANB11', 'TAEE11', 'ALUP11', 'ENGI11', 'SAPR11', 'KLBN11', 'IGTI11']:
            setor = "Fundos Imobiliários (FII)"
        else:
            if info.get('quoteType') == 'ETF':
                setor = "ETFs"
            else:
                setor_eng = info.get('sector')
                if setor_eng: 
                    setor = MAPA_SETORES_PT.get(setor_eng, setor_eng)
        
        # BUSCA DE P/VP PARA BDRs E AÇÕES
        tipo = identificar_tipo_ativo(ticker)
        if tipo == 'BDR':
            ticker_base = MAPA_BDR_BASE.get(ticker.upper())
            if ticker_base:
                try:
                    info_base = yf.Ticker(ticker_base).info
                    pvp = info_base.get('priceToBook')
                    if pvp is None:
                        preco = info_base.get('currentPrice') or info_base.get('regularMarketPrice')
                        book_ps = info_base.get('bookValue') or info_base.get('bookValuePerShare')
                        if preco and book_ps and book_ps != 0:
                            pvp = preco / book_ps
                except: pass
        else:
            pvp = info.get("priceToBook")

        dy = info.get("dividendYield")
        margem_ebit = info.get("operatingMargins")
        margem_liq = info.get("profitMargins")
        roe = info.get("returnOnEquity")
        roa = info.get("returnOnAssets")
        
        total_debt = info.get("totalDebt")
        cash = info.get("totalCash")
        ebitda = info.get("ebitda")
        
        div_liq_ebitda = None
        if total_debt and ebitda and ebitda != 0:
            div_liq_ebitda = (total_debt - (cash or 0)) / ebitda

        return {
            "Ativo": ticker,
            "Setor": setor,
            "P/L": float(pl) if pl else np.nan,
            "P/VP": float(pvp) if pvp else np.nan,
            "DY": float(dy) if dy else np.nan,
            "D.L./EB": float(div_liq_ebitda) if div_liq_ebitda else np.nan,
            "M.EBIT": float(margem_ebit * 100) if margem_ebit else np.nan,
            "M.Líq": float(margem_liq * 100) if margem_liq else np.nan,
            "ROA (%)": float(roa * 100) if roa else np.nan,
            "ROE (%)": float(roe * 100) if roe else np.nan
        }
    except:
        return {
            "Ativo": ticker, "Setor": "Outros", "P/L": np.nan, "P/VP": np.nan, "DY": np.nan,
            "D.L./EB": np.nan, "M.EBIT": np.nan, "M.Líq": np.nan, "ROA (%)": np.nan, "ROE (%)": np.nan
        }
    
def media_ponderada(serie, pesos):
    df_temp = pd.DataFrame({'valor': serie, 'peso': pesos}).dropna()
    if df_temp.empty or df_temp['peso'].sum() == 0: return np.nan
    return np.average(df_temp['valor'], weights=df_temp['peso'])

def plotar_tabela_multiplos(posicao, arquivo_ibov):
    st.subheader("📊 Tabela de Múltiplos e Valuation")
    
    with st.spinner("Calculando múltiplos fundamentalistas (Carteira vs IBOV). Isso pode levar alguns segundos..."):
        tabela_ativos = posicao.copy()
        tickers_carteira = tabela_ativos["Ticker"].dropna().unique().tolist()
        
        lista_multiplos = []
        for ticker in tickers_carteira:
            lista_multiplos.append(buscar_multiplos(ticker))
            
        df_multiplos = pd.DataFrame(lista_multiplos).set_index("Ativo")
        pesos_cart = tabela_ativos.groupby("Ticker")["% na Carteira"].sum() / 100
        
        mult_carteira = {
            "Ativo": "CARTEIRA",
            "Setor": "-",
            "P/L": media_ponderada(df_multiplos["P/L"], pesos_cart),
            "P/VP": media_ponderada(df_multiplos["P/VP"], pesos_cart),
            "DY": media_ponderada(df_multiplos["DY"], pesos_cart),
            "D.L./EB": media_ponderada(df_multiplos["D.L./EB"], pesos_cart),
            "M.EBIT": media_ponderada(df_multiplos["M.EBIT"], pesos_cart),
            "M.Líq": media_ponderada(df_multiplos["M.Líq"], pesos_cart),
            "ROA (%)": media_ponderada(df_multiplos["ROA (%)"], pesos_cart),
            "ROE (%)": media_ponderada(df_multiplos["ROE (%)"], pesos_cart),
        }
        
        mult_ibov = {col: np.nan for col in mult_carteira}
        mult_ibov["Ativo"] = "IBOVESPA"
        mult_ibov["Setor"] = "-"
        df_ibov_mult = pd.DataFrame()
        
        if arquivo_ibov and os.path.exists(arquivo_ibov):
            try:
                try:
                    df_ibov_comp = pd.read_csv(arquivo_ibov, sep=";", encoding="latin1", skiprows=1)
                    if len(df_ibov_comp.columns) < 2:
                        df_ibov_comp = pd.read_csv(arquivo_ibov, sep=";", encoding="latin1")
                except:
                    df_ibov_comp = pd.read_csv(arquivo_ibov, sep=";", encoding="latin1")
                
                col_ativo = [c for c in df_ibov_comp.columns if 'ativo' in c.lower() or 'código' in c.lower()]
                col_peso = [c for c in df_ibov_comp.columns if 'part' in c.lower() or 'peso' in c.lower()]
                
                if col_ativo and col_peso:
                    ativos_ibov = df_ibov_comp[col_ativo[0]].dropna().astype(str)
                    pesos_ibov_raw = df_ibov_comp[col_peso[0]].astype(str).str.replace(',', '.').replace('', '0')
                    df_ibov_clean = pd.DataFrame({'Ativo': ativos_ibov, 'Peso': pd.to_numeric(pesos_ibov_raw, errors='coerce')}).dropna()
                    
                    lista_ibov = []
                    for ativo in df_ibov_clean["Ativo"]:
                        lista_ibov.append(buscar_multiplos(ativo))
                        
                    df_ibov_mult = pd.DataFrame(lista_ibov).set_index("Ativo")
                    pesos_ibov = df_ibov_clean.groupby("Ativo")["Peso"].sum() / 100
                    
                    mult_ibov = {
                        "Ativo": "IBOVESPA",
                        "Setor": "-",
                        "P/L": media_ponderada(df_ibov_mult["P/L"], pesos_ibov),
                        "P/VP": media_ponderada(df_ibov_mult["P/VP"], pesos_ibov),
                        "DY": media_ponderada(df_ibov_mult["DY"], pesos_ibov),
                        "D.L./EB": media_ponderada(df_ibov_mult["D.L./EB"], pesos_ibov),
                        "M.EBIT": media_ponderada(df_ibov_mult["M.EBIT"], pesos_ibov),
                        "M.Líq": media_ponderada(df_ibov_mult["M.Líq"], pesos_ibov),
                        "ROA (%)": media_ponderada(df_ibov_mult["ROA (%)"], pesos_ibov),
                        "ROE (%)": media_ponderada(df_ibov_mult["ROE (%)"], pesos_ibov),
                    }
            except: pass
            
        df_multiplos.reset_index(inplace=True)
        
        if not df_ibov_mult.empty:
            df_ibov_mult.reset_index(inplace=True)
            df_todos_ativos = pd.concat([df_multiplos, df_ibov_mult]).drop_duplicates(subset=['Ativo'])
        else:
            df_todos_ativos = df_multiplos

        df_todos_ativos = df_todos_ativos.sort_values(by="Ativo")

        df_final = pd.concat([pd.DataFrame([mult_carteira]), pd.DataFrame([mult_ibov]), df_todos_ativos], ignore_index=True)
        
        def destacar_linhas(row):
            ativo = row['Ativo']
            if ativo == 'CARTEIRA':
                return ['background-color: #002244; color: white; font-weight: bold'] * len(row)
            elif ativo == 'IBOVESPA':
                return ['background-color: #4b5563; color: white; font-weight: bold'] * len(row)
            elif ativo in tickers_carteira:
                return ['background-color: #059669; color: white; font-weight: bold'] * len(row)
            return [''] * len(row)

        df_styled = df_final.style.apply(destacar_linhas, axis=1)

        st.dataframe(
            df_styled, 
            use_container_width=True,
            hide_index=True,
            column_config={
                "Ativo": st.column_config.TextColumn("Ativo"),
                "Setor": st.column_config.TextColumn("Setor"),
                "P/L": st.column_config.NumberColumn("P/L", format="%.2f"),
                "P/VP": st.column_config.NumberColumn("P/VP", format="%.2f"),
                "DY": st.column_config.NumberColumn("DY", format="%.2f%%"),
                "D.L./EB": st.column_config.NumberColumn("D.L./EB", format="%.2f"),
                "M.EBIT": st.column_config.NumberColumn("M.EBIT", format="%.2f%%"),
                "M.Líq": st.column_config.NumberColumn("M.Líq", format="%.2f%%"),
                "ROA (%)": st.column_config.NumberColumn("ROA (%)", format="%.2f%%"),
                "ROE (%)": st.column_config.NumberColumn("ROE (%)", format="%.2f%%"),
            }
        )