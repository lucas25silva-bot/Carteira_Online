import pandas as pd
import yfinance as yf
import numpy as np
import streamlit as st
import os

# ========================================================
# MAPAS DE SETORES PARA AGRUPAMENTO RÁPIDO
# ========================================================
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

def fast_sector_mapper(ticker):
    t_str = str(ticker).upper()
    if t_str == 'IBOVESPA': return 'Índice'
    if t_str in MAPA_B3_SETOR: return MAPA_B3_SETOR[t_str]
    if t_str.endswith('34') or t_str.endswith('33') or t_str.endswith('35') or t_str.endswith('39'): return 'Exterior (BDR)'
    if t_str in ['BOVA11', 'IVVB11', 'SMAL11', 'HASH11', 'NASD11']: return 'ETFs'
    if t_str.endswith('11'): return 'Fundos Imobiliários (FII)'
    return 'Outros'

@st.cache_data(show_spinner=False, ttl=3600)
def carregar_dados_retornos(tickers_carteira_tuple, arquivo_ibov):
    todos_tickers = set(tickers_carteira_tuple)
    
    # 1. Adiciona os ativos do IBOV
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
        
    tickers_yf = [f"{t}.SA" for t in list(todos_tickers)]
    tickers_yf.append("^BVSP")
    
    # 2. Baixa o histórico
    hist = yf.download(tickers_yf, period='5y', progress=False)
    
    if 'Adj Close' in hist.columns:
        hist = hist['Adj Close']
    elif 'Close' in hist.columns:
        hist = hist['Close']
        
    if isinstance(hist, pd.Series):
        hist = hist.to_frame()
        
    hist.columns = [str(c).replace('.SA', '') if str(c) != '^BVSP' else 'IBOVESPA' for c in hist.columns]
    
    if hist.index.tz is not None:
        hist.index = hist.index.tz_localize(None)
        
    # 3. Define datas alvo
    hoje = pd.Timestamp.today()
    ultimo_dia_mes_ant = hoje.replace(day=1) - pd.Timedelta(days=1)
    ultimo_dia_ano_ant = hoje.replace(month=1, day=1) - pd.Timedelta(days=1)
    
    datas_alvo = {
        'No Mês': ultimo_dia_mes_ant,
        '1 Mês': hoje - pd.DateOffset(months=1),
        '3 Meses': hoje - pd.DateOffset(months=3),
        '6 Meses': hoje - pd.DateOffset(months=6),
        'No Ano': ultimo_dia_ano_ant,
        '12 Meses': hoje - pd.DateOffset(months=12),
        '24 Meses': hoje - pd.DateOffset(months=24),
        '36 Meses': hoje - pd.DateOffset(months=36),
        '60 Meses': hoje - pd.DateOffset(months=60)
    }
    
    # 4. Calcula retornos
    dados = []
    colunas_ativos = hist.columns
    
    for ticker in colunas_ativos:
        try:
            s = hist[ticker].dropna()
            if s.empty: continue
                
            p_atual = s.iloc[-1]
            data_inicial_ativo = s.index[0]
            
            res = {'Ativo': ticker}
            for label, data_alvo in datas_alvo.items():
                if data_alvo >= data_inicial_ativo:
                    p_passado = s.asof(data_alvo)
                    if pd.notna(p_passado) and p_passado > 0:
                        res[label] = (p_atual / p_passado) - 1
                    else:
                        res[label] = np.nan
                else:
                    res[label] = np.nan
                    
            dados.append(res)
        except: pass
            
    df_final = pd.DataFrame(dados)
    
    # ==========================================
    # CÁLCULO DA NOTA DE RETORNO (MOMENTUM CONTRÁRIO)
    # ==========================================
    df_final['Setor'] = df_final['Ativo'].apply(fast_sector_mapper)
    
    # PESOS DAS JANELAS
    PESOS_JANELAS = {
        'No Mês': 0,
        '1 Mês': 5,
        '3 Meses': 5,
        '6 Meses': 10,
        'No Ano': 5,
        '12 Meses': 15,
        '24 Meses': 15,
        '36 Meses': 20,
        '60 Meses': 25
    }
    
    soma_pesos = sum(PESOS_JANELAS.values())
    nota_acumulada = 0
    
    for janela, peso in PESOS_JANELAS.items():
        if peso > 0:
            rank_janela = df_final.groupby('Setor')[janela].rank(pct=True, ascending=False) * 10
            nota_acumulada += rank_janela.fillna(0) * peso
            
    df_final['Nota Retorno'] = nota_acumulada / soma_pesos
    # ==========================================
    
    # Ordenação (Mantemos a coluna 'Setor' viva agora)
    df_final['is_ibov'] = df_final['Ativo'] == 'IBOVESPA'
    df_final = df_final.sort_values(by=['is_ibov', '12 Meses'], ascending=[False, False]).drop(columns=['is_ibov'])
    
    return df_final


def plotar_tabela_retornos(posicao, arquivo_ibov):
    st.subheader("Tabela de Retornos Históricos")
    
    tickers_carteira = posicao["Ticker"].dropna().unique().tolist()
    
    with st.spinner("Baixando histórico de 5 anos e calculando Score de Desconto..."):
        df_final = carregar_dados_retornos(tuple(tickers_carteira), arquivo_ibov)
        
    # Dois Filtros Lado a Lado
    col1, col2 = st.columns(2)
    opcoes_setores = sorted([s for s in df_final["Setor"].unique() if pd.notna(s) and s != 'Índice'])
    opcoes_ativos = sorted([a for a in df_final["Ativo"].unique() if pd.notna(a)])

    with col1:
        filtro_setor = st.multiselect("Filtrar por Setor:", options=opcoes_setores, placeholder="Todos os setores...")
    with col2:
        filtro_ativo = st.multiselect("Filtrar por Ativo:", options=opcoes_ativos, placeholder="Todos os ativos...")

    # Aplicação dos filtros
    df_filtrado = df_final.copy()
    if filtro_setor:
        df_filtrado = df_filtrado[(df_filtrado["Setor"].isin(filtro_setor)) | (df_filtrado["Ativo"] == "IBOVESPA")]
    if filtro_ativo:
        df_filtrado = df_filtrado[(df_filtrado["Ativo"].isin(filtro_ativo)) | (df_filtrado["Ativo"] == "IBOVESPA")]

    def aplicar_estilos(row):
        estilos = [''] * len(row)
        is_carteira = row['Ativo'] in tickers_carteira
        is_ibov = row['Ativo'] == 'IBOVESPA'
        
        for i, col in enumerate(row.index):
            if col in ['Ativo', 'Setor']:
                if is_carteira:
                    estilos[i] = 'background-color: #059669; color: white; font-weight: bold'
                elif is_ibov:
                    estilos[i] = 'background-color: #4b5563; color: white; font-weight: bold'
            elif col != 'Nota Retorno': 
                val = row[col]
                bg_color = ''
                if is_carteira: bg_color = 'background-color: #059669;'
                elif is_ibov: bg_color = 'background-color: #4b5563;'
                
                text_color = ''
                if is_carteira or is_ibov:
                    text_color = 'color: white; font-weight: bold;'
                else:
                    if pd.notna(val):
                        if val > 0: text_color = 'color: #2563eb; font-weight: bold;'
                        elif val < 0: text_color = 'color: #ef4444; font-weight: bold;'
                            
                estilos[i] = f"{bg_color} {text_color}".strip()
                
        return estilos

    def formatar_retorno(val):
        if pd.isna(val): return "-"
        if val > 0: return f"↑ {val*100:.2f}%"
        elif val < 0: return f"↓ {abs(val*100):.2f}%"
        return f"{val*100:.2f}%"

    colunas_retorno = ['No Mês', '1 Mês', '3 Meses', '6 Meses', 'No Ano', '12 Meses', '24 Meses', '36 Meses', '60 Meses']
    formatadores = {col: formatar_retorno for col in colunas_retorno}
    
    df_styled = df_filtrado.style.apply(aplicar_estilos, axis=1).format(formatadores)
    
    # Configuração das Colunas no Streamlit (Exibe Setor, esconde a Nota)
    col_config = {
        "Ativo": st.column_config.TextColumn("Ativo"),
        "Setor": st.column_config.TextColumn("Setor"),
        "Nota Retorno": None  # Oculta da visão, mas o dataframe retornado ainda a possui!
    }
    
    for col in colunas_retorno:
        col_config[col] = st.column_config.Column(col)

    st.dataframe(
        df_styled,
        use_container_width=True,
        hide_index=True,
        column_config=col_config
    )
    
    # Retorna o Dataframe Final intacto para o próximo módulo usar
    return df_final