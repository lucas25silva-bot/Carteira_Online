import pandas as pd
import yfinance as yf
import numpy as np
import streamlit as st
import os

MAPA_SETORES_PT = {
    'Financial Services': 'Financeiro', 'Healthcare': 'Saúde', 'Technology': 'Tecnologia',
    'Industrials': 'Bens Industriais', 'Consumer Cyclical': 'Consumo Cíclico',
    'Consumer Defensive': 'Consumo Não Cíclico', 'Basic Materials': 'Materiais Básicos',
    'Energy': 'Petróleo e Gás', 'Utilities': 'Utilidade Pública', 'Real Estate': 'Consumo Cíclico',
    'Communication Services': 'Comunicações'
}

MAPA_B3_SETOR = {

        # FINANCEIRO
        'ITSA4': 'Financeiro', 'ITUB4': 'Financeiro', 'BBDC4': 'Financeiro',
        'BBAS3': 'Financeiro', 'B3SA3': 'Financeiro', 'BPAC11': 'Financeiro',
        'SANB11': 'Financeiro', 'BBSE3': 'Financeiro', 'CXSE3': 'Financeiro',
        'IRBR3': 'Financeiro', 'BRSR6': 'Financeiro', 'ABCB4': 'Financeiro',

        # UTILIDADE PÚBLICA (energia + saneamento juntos, padrão B3)
        'ELET3': 'Utilidade Pública', 'ELET6': 'Utilidade Pública',
        'EQTL3': 'Utilidade Pública', 'CPLE6': 'Utilidade Pública',
        'CMIG4': 'Utilidade Pública', 'ENGI11': 'Utilidade Pública',
        'TAEE11': 'Utilidade Pública', 'TRPL4': 'Utilidade Pública',
        'ALUP11': 'Utilidade Pública', 'EGIE3': 'Utilidade Pública',
        'NEOE3': 'Utilidade Pública', 'AURE3': 'Utilidade Pública',
        'SBSP3': 'Utilidade Pública', 'CSMG3': 'Utilidade Pública',
        'SAPR11': 'Utilidade Pública', 'SAPR4': 'Utilidade Pública',

        # PETRÓLEO E GÁS
        'PETR4': 'Petróleo e Gás', 'PETR3': 'Petróleo e Gás',
        'PRIO3': 'Petróleo e Gás', 'RECV3': 'Petróleo e Gás',
        'ENAT3': 'Petróleo e Gás', 'CSAN3': 'Petróleo e Gás',
        'UGPA3': 'Petróleo e Gás', 'VBBR3': 'Petróleo e Gás',

        # MATERIAIS BÁSICOS
        'VALE3': 'Materiais Básicos', 'SUZB3': 'Materiais Básicos',
        'KLBN11': 'Materiais Básicos', 'CSNA3': 'Materiais Básicos',
        'GGBR4': 'Materiais Básicos', 'GOAU4': 'Materiais Básicos',
        'USIM5': 'Materiais Básicos', 'BRAP4': 'Materiais Básicos',
        'CMIN3': 'Materiais Básicos', 'CBAV3': 'Materiais Básicos',
        'DXCO3': 'Materiais Básicos',

        # INDUSTRIAL
        'WEGE3': 'Bens Industriais', 'EMBR3': 'Bens Industriais',
        'CCRO3': 'Bens Industriais', 'RAIL3': 'Bens Industriais',
        'AZUL4': 'Bens Industriais', 'GOLL4': 'Bens Industriais',
        'STBP3': 'Bens Industriais', 'POMO4': 'Bens Industriais',
        'TUPY3': 'Bens Industriais', 'MILS3': 'Bens Industriais',

        # CONSUMO CÍCLICO
        'LREN3': 'Consumo Cíclico', 'MGLU3': 'Consumo Cíclico',
        'ARZZ3': 'Consumo Cíclico', 'PETZ3': 'Consumo Cíclico',
        'SOMA3': 'Consumo Cíclico', 'CEAB3': 'Consumo Cíclico',
        'CVCB3': 'Consumo Cíclico', 'COGN3': 'Consumo Cíclico',
        'YDUQ3': 'Consumo Cíclico', 'RENT3': 'Consumo Cíclico',
        'MOVI3': 'Consumo Cíclico', 'VIVA3': 'Consumo Cíclico',
        'MULT3': 'Consumo Cíclico', 'IGTI11': 'Consumo Cíclico',
        'CYRE3': 'Consumo Cíclico', 'EZTC3': 'Consumo Cíclico',
        'MRVE3': 'Consumo Cíclico', 'DIRR3': 'Consumo Cíclico',
        'JHSF3': 'Consumo Cíclico', 'HBOR3': 'Consumo Cíclico',

        # CONSUMO NÃO CÍCLICO
        'ABEV3': 'Consumo Não Cíclico', 'JBSS3': 'Consumo Não Cíclico',
        'BRFS3': 'Consumo Não Cíclico', 'CRFB3': 'Consumo Não Cíclico',
        'ASAI3': 'Consumo Não Cíclico', 'SMTO3': 'Consumo Não Cíclico',
        'SLCE3': 'Consumo Não Cíclico', 'MRFG3': 'Consumo Não Cíclico',
        'BEEF3': 'Consumo Não Cíclico', 'PCAR3': 'Consumo Não Cíclico',
        'CAML3': 'Consumo Não Cíclico',

        # SAÚDE
        'RADL3': 'Saúde', 'RDOR3': 'Saúde', 'HAPV3': 'Saúde',
        'FLRY3': 'Saúde', 'MATD3': 'Saúde', 'QUAL3': 'Saúde',
        'BLAU3': 'Saúde', 'VVEO3': 'Saúde', 'PNVL3': 'Saúde',

        # TECNOLOGIA
        'TOTS3': 'Tecnologia', 'LWSA3': 'Tecnologia',

        # COMUNICAÇÕES
        'VIVT3': 'Comunicações', 'TIMS3': 'Comunicações',

        'ENEV3': 'Utilidade Pública',
        'AXIA3': 'Utilidade Pública',
        'AXIA6': 'Utilidade Pública',
        'AXIA7': 'Utilidade Pública',
        'CPLE3': 'Utilidade Pública',
        'ISAE4': 'Utilidade Pública',

        'CURY3': 'Consumo Cíclico',
        'ALOS3': 'Consumo Cíclico',
        'AZZA3': 'Consumo Cíclico',
        'SMFT3': 'Consumo Cíclico',
        'VAMO3': 'Consumo Cíclico',
        'CYRE4': 'Consumo Cíclico',
        'RENT4': 'Consumo Cíclico',

        'BBDC3': 'Financeiro',
        'PSSA3': 'Financeiro',

        'MILS3': 'Bens Industriais',
        'MOTV3': 'Bens Industriais',

        'HYPE3': 'Saúde',

        'BRKM5': 'Materiais Básicos',

        'BRAV3': 'Petróleo e Gás',
        'RAIZ4': 'Petróleo e Gás',

        'MRFG3': 'Consumo Não Cíclico',
        'NTCO3': 'Consumo Não Cíclico'

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

def buscar_dados_target(ticker):
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
        preco = info.get('currentPrice') or info.get('regularMarketPrice')
        alvo = info.get('targetMeanPrice')
        recomendacao = info.get('recommendationKey', "N/A")
        upside = np.nan
        
        if tipo == 'BDR':
            ticker_base = MAPA_BDR_BASE.get(ticker.upper())
            if ticker_base:
                try:
                    info_base = yf.Ticker(ticker_base).info
                    preco_us = info_base.get('currentPrice') or info_base.get('regularMarketPrice')
                    alvo_us = info_base.get('targetMeanPrice')
                    recomendacao = info_base.get('recommendationKey', recomendacao)
                    if preco_us and alvo_us and preco_us > 0:
                        upside = (alvo_us / preco_us) - 1
                        if preco and not pd.isna(upside):
                            alvo = preco * (1 + upside)
                except: pass
        else:
            if preco and alvo and preco > 0:
                upside = (alvo / preco) - 1

        rec_map = {
            "buy": "Compra", "strong_buy": "Forte Compra", 
            "hold": "Manter", "underperform": "Abaixo da Média", 
            "sell": "Venda", "strong_sell": "Forte Venda"
        }
        recomendacao_pt = rec_map.get(str(recomendacao).lower(), "N/A")

        return {
            "Ativo": ticker,
            "Setor": setor,
            "Preço Atual": float(preco) if preco is not None else np.nan,
            "Preço Alvo": float(alvo) if alvo is not None else np.nan,
            "Upside (%)": float(upside * 100) if not pd.isna(upside) else np.nan,
            "Recomendação": recomendacao_pt
        }
    except Exception:
        return {
            "Ativo": ticker, "Setor": "Outros", 
            "Preço Atual": np.nan, "Preço Alvo": np.nan, 
            "Upside (%)": np.nan, "Recomendação": "N/A"
        }

@st.cache_data(show_spinner=False, ttl=3600)
def carregar_dados_target_cache(tickers_carteira_tuple, arquivo_ibov):
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
        dados.append(buscar_dados_target(t))
        
    df_final = pd.DataFrame(dados)
    
    # ==========================================
    # NOVO: CÁLCULO DA NOTA DE UPSIDE (0 a 10)
    # ==========================================
    # Aplica o rankeamento agrupado por setor (quanto maior o upside, melhor a nota)
    df_final['Nota Upside'] = (df_final.groupby('Setor')['Upside (%)'].rank(pct=True, ascending=True) * 10).fillna(0)
    
    # Ordenação final
    df_final = df_final.sort_values(by=["Setor", "Upside (%)"], ascending=[True, False])
    
    return df_final


def plotar_tabela_target(posicao, arquivo_ibov):
    st.subheader("Tabela de Target Price (Preço Alvo e Upside)")
    
    tickers_carteira = posicao["Ticker"].dropna().unique().tolist()
    
    with st.spinner("Buscando projeções de mercado e calculando Upside..."):
        df_final = carregar_dados_target_cache(tuple(tickers_carteira), arquivo_ibov)
        
    col1, col2 = st.columns(2)
    opcoes_setores = sorted([s for s in df_final["Setor"].unique() if pd.notna(s)])
    opcoes_ativos = sorted([a for a in df_final["Ativo"].unique() if pd.notna(a)])

    with col1:
        filtro_setor = st.multiselect("Filtrar Target por Setor:", options=opcoes_setores, placeholder="Todos os setores...")
    with col2:
        filtro_ativo = st.multiselect("Filtrar Target por Ativo:", options=opcoes_ativos, placeholder="Todos os ativos...")

    # Aplicação dos filtros
    df_filtrado = df_final.copy()
    if filtro_setor:
        df_filtrado = df_filtrado[df_filtrado["Setor"].isin(filtro_setor)]
    if filtro_ativo:
        df_filtrado = df_filtrado[df_filtrado["Ativo"].isin(filtro_ativo)]

    def aplicar_estilos(row):
        estilos = [''] * len(row)
        idx_upside = row.index.get_loc('Upside (%)')
        is_carteira = row['Ativo'] in tickers_carteira
        upside = row['Upside (%)']
        
        for i in range(len(row)):
            if is_carteira:
                estilos[i] = 'background-color: #059669; color: white; font-weight: bold'
            else:
                if i == idx_upside and pd.notna(upside):
                    if upside > 0:
                        estilos[i] = 'color: #2563eb; font-weight: bold' 
                    elif upside < 0:
                        estilos[i] = 'color: #ef4444; font-weight: bold' 
        return estilos

    def formatar_upside(val):
        if pd.isna(val):
            return "-"
        if val > 0:
            return f"↑ {val:.2f}%"
        elif val < 0:
            return f"↓ {abs(val):.2f}%"
        return f"{val:.2f}%"

    df_styled = df_filtrado.style.apply(aplicar_estilos, axis=1).format({'Upside (%)': formatar_upside})
    
    st.dataframe(
        df_styled,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Ativo": st.column_config.TextColumn("Ativo"),
            "Setor": st.column_config.TextColumn("Setor"),
            "Preço Atual": st.column_config.NumberColumn("Preço Atual", format="R$ %.2f"),
            "Preço Alvo": st.column_config.NumberColumn("Preço Alvo", format="R$ %.2f"),
            "Upside (%)": st.column_config.Column("Upside Estimado"),
            
            # ATENÇÃO: A coluna abaixo oculta a "Nota Upside" da vista, 
            # mas ela continua a existir no dataframe base (df_final) para uso futuro.
            "Nota Upside": None
        }
    )
    
    # Opcional: Se for precisar importar df_final em outro módulo diretamente daqui,
    # pode ser interessante retornar df_final no final desta função no futuro!
    return df_final