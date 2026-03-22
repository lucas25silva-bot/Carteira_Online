import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
from datetime import datetime, timedelta

@st.cache_data(show_spinner=False, ttl=3600)
def processar_alocacao_tempo_setor(arquivo_carteira):
    df_neg = pd.read_excel(arquivo_carteira, sheet_name='Negociação')
    df_neg['Data do Negócio'] = pd.to_datetime(df_neg['Data do Negócio'], dayfirst=True)
    df_neg['Ticker'] = df_neg['Código de Negociação'].str.replace('F$', '', regex=True)
    df_neg['Quantidade'] = pd.to_numeric(df_neg['Quantidade'], errors='coerce').fillna(0)
    
    df_neg['Qtd_Sinal'] = np.where(
        df_neg['Tipo de Movimentação'].str.upper().str.contains('COMPRA'),
        df_neg['Quantidade'], -df_neg['Quantidade']
    )
    
    trades_pivot = df_neg.pivot_table(index='Data do Negócio', columns='Ticker', values='Qtd_Sinal', aggfunc='sum').fillna(0)
    
    data_ini = df_neg['Data do Negócio'].min()
    data_fim = datetime.today()
    datas = pd.date_range(start=data_ini, end=data_fim, freq='B')
    
    trades_reindexed = trades_pivot.reindex(datas).fillna(0)
    posicoes_diarias = trades_reindexed.cumsum()
    
    tickers_yf = [f"{t}.SA" for t in posicoes_diarias.columns]
    
    try:
        dados_raw = yf.download(tickers_yf, start=data_ini - timedelta(days=5), end=data_fim + timedelta(days=1), progress=False)
        if isinstance(dados_raw.columns, pd.MultiIndex):
            dados_mkt = dados_raw['Close'] if 'Close' in dados_raw.columns.get_level_values(0) else dados_raw
        elif 'Close' in dados_raw.columns:
            dados_mkt = dados_raw[['Close']].rename(columns={'Close': tickers_yf[0]}) if len(tickers_yf) == 1 else dados_raw
        else:
            dados_mkt = dados_raw
    except:
        dados_mkt = pd.DataFrame()

    if dados_mkt.index.tz is not None:
        dados_mkt.index = dados_mkt.index.tz_localize(None)
        
    dados_mkt.columns = [str(c).replace('.SA', '') for c in dados_mkt.columns]
    dados_mkt = dados_mkt.reindex(datas).ffill()
    
    cols_comuns = posicoes_diarias.columns.intersection(dados_mkt.columns)
    posicoes_diarias = posicoes_diarias[cols_comuns]
    dados_mkt = dados_mkt[cols_comuns]
    
    valor_diario = posicoes_diarias * dados_mkt
    valor_diario = valor_diario.fillna(0)
    valor_diario[valor_diario < 0] = 0 
    
    # =========================================================
    # LÓGICA DE MAPEAMENTO DE SETORES IDÊNTICA AO GRÁFICO DE FUNIL
    # =========================================================
    mapa_setores_pt = {
    'Financial Services': 'Financeiro', 'Healthcare': 'Saúde', 'Technology': 'Tecnologia',
    'Industrials': 'Bens Industriais', 'Consumer Cyclical': 'Consumo Cíclico',
    'Consumer Defensive': 'Consumo Não Cíclico', 'Basic Materials': 'Materiais Básicos',
    'Energy': 'Petróleo e Gás', 'Utilities': 'Utilidade Pública', 'Real Estate': 'Consumo Cíclico',
    'Communication Services': 'Comunicações'
}

    mapa_b3_setor = {

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

    def classificar_setor(t):
        if t in mapa_b3_setor:
            return mapa_b3_setor[t]
        elif t[-2:] in ['33', '34', '35', '39']:
            return "Exterior (BDR)"
        elif t in ['BOVA11', 'IVVB11', 'SMAL11', 'HASH11', 'NASD11', 'DIVO11', 'FIXA11', 'BINA11', 'XINA11', 'GOLD11']:
            return "ETFs"
        elif t.endswith('11') and t not in ['BPAC11', 'SANB11', 'TAEE11', 'ALUP11', 'ENGI11', 'SAPR11', 'KLBN11', 'IGTI11']:
            return "Fundos Imobiliários (FII)"
        else:
            try:
                info = yf.Ticker(f"{t}.SA").info
                if info.get('quoteType') == 'ETF':
                    return "ETFs"
                else:
                    setor_eng = info.get('sector')
                    if setor_eng:
                        return mapa_setores_pt.get(setor_eng, setor_eng)
            except:
                pass
        return "Outros"

    # Aplica o mapa para cruzar ativo x setor
    dict_setores = {t: classificar_setor(t) for t in cols_comuns}
    
    # Agrupa todo o dinheiro somando pelos setores diários
    valor_diario_setor = valor_diario.rename(columns=dict_setores).groupby(level=0, axis=1).sum()
    
    total_diario = valor_diario_setor.sum(axis=1)
    perc_diario = valor_diario_setor.div(total_diario, axis=0) * 100
    perc_diario = perc_diario.fillna(0)
    
    df_plot = perc_diario.reset_index().melt(id_vars='index', var_name='Setor', value_name='Perc')
    df_plot.rename(columns={'index': 'Data'}, inplace=True)
    df_plot = df_plot[df_plot['Perc'] > 0]
    
    return df_plot

def plotar_alocacao_tempo(arquivo_carteira):
    st.markdown("---")
    st.subheader("Evolução da Alocação da Carteira por Setor (%)")
    
    with st.spinner("Calculando o histórico diário de pesos dos setores..."):
        df_plot = processar_alocacao_tempo_setor(arquivo_carteira)
        
    if not df_plot.empty:
        # ========================================================
        # O MESMO DICIONÁRIO DE CORES DO GRÁFICO DE FUNIL
        # ========================================================
        MAPA_CORES_SETORES = {
            'Financeiro': '#3A86FF',
            'Energia Elétrica': '#FFBE0B',
            'Petróleo e Gás': '#FB5607',
            'Materiais Básicos / Siderurgia': '#8338EC',
            'Bens Industriais': '#8D6E63',
            'Consumo Cíclico': "#C0131B",
            'Consumo Não Cíclico': '#2ECC71',
            'Saúde': '#06D6A0',
            'Tecnologia': '#00BBF9',
            'Comunicações': '#F15BB5',
            'Imobiliário': '#F8961E',
            'Saneamento': '#4CC9F0',
            'Fundos Imobiliários (FII)': '#7209B7',
            'Exterior (BDR)': '#90DBF4',
            'ETFs': '#43AA8B',
            'Outros': '#ADB5BD'
        }

        fig = px.area(
            df_plot, 
            x="Data", 
            y="Perc", 
            color="Setor",
            color_discrete_map=MAPA_CORES_SETORES # <-- Cores sincronizadas com o Funil!
        )
        
        fig.update_traces(
            hovertemplate="<b>%{data.name}</b><br>Peso: %{y:.2f}%<extra></extra>",
            line=dict(width=0) 
        )
        
        fig.update_layout(
            xaxis_title="",
            yaxis_title="<b>% do Patrimônio</b>",
            hovermode="x unified",
            legend_title="Setor",
            height=500,
            margin=dict(l=40, r=40, t=20, b=40),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(range=[0, 100], showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
            xaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Não há dados suficientes para montar o histórico de alocação.")