import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import timedelta

@st.cache_data(show_spinner=False, ttl=3600)
def calcular_evolucao_patrimonio(arquivo_carteira):
    def limpar_moeda(valor):
        if pd.isna(valor): return 0.0
        if isinstance(valor, str):
            valor = valor.replace('R$', '').replace('.', '').replace(',', '.')
        try:
            return float(valor)
        except:
            return 0.0

    # 1. Lê a aba de negociação
    df_neg = pd.read_excel(arquivo_carteira, sheet_name='Negociação')
    df_neg['Data do Negócio'] = pd.to_datetime(df_neg['Data do Negócio'], dayfirst=True)
    df_neg['Ticker'] = df_neg['Código de Negociação'].str.replace('F$', '', regex=True)
    df_neg['Valor'] = df_neg['Valor'].apply(limpar_moeda)

    df_neg['Valor_Sinal'] = np.where(
        df_neg['Tipo de Movimentação'].str.upper().str.contains('COMPRA'),
        df_neg['Valor'], -df_neg['Valor']
    )
    df_neg['Qtd_Sinal'] = np.where(
        df_neg['Tipo de Movimentação'].str.upper().str.contains('COMPRA'),
        df_neg['Quantidade'], -df_neg['Quantidade']
    )

    # 2. Lê a aba de Proventos Recebidos
    try:
        df_prov = pd.read_excel(arquivo_carteira, sheet_name='Proventos Recebidos')
        if not df_prov.empty:
            col_valor = [c for c in df_prov.columns if 'Valor' in c][0]
            col_data = [c for c in df_prov.columns if 'Data' in c or 'Pagamento' in c][0]
            df_prov[col_data] = pd.to_datetime(df_prov[col_data], dayfirst=True)
            df_prov['Valor_Real'] = df_prov[col_valor].apply(limpar_moeda)
            div_por_dia = df_prov.groupby(col_data)['Valor_Real'].sum()
        else:
            div_por_dia = pd.Series(dtype=float)
    except:
        div_por_dia = pd.Series(dtype=float)

    data_ini = df_neg['Data do Negócio'].min()
    tickers = [f"{t}.SA" for t in df_neg['Ticker'].unique()]
    
    # 3. Baixa as cotações do Yahoo Finance
    dados_mkt = yf.download(
        tickers + ['^BVSP'], 
        start=data_ini - timedelta(days=5),
        progress=False
    )['Close']

    if dados_mkt.index.tz is not None:
        dados_mkt.index = dados_mkt.index.tz_localize(None)

    datas = pd.date_range(start=data_ini, end=dados_mkt.index.max(), freq='B')
    dados_mkt = dados_mkt.reindex(datas).ffill()

    # 4. Alinha os proventos ao calendário e faz a soma cumulativa
    div_diario = div_por_dia.reindex(datas).fillna(0)
    proventos_acumulados_serie = div_diario.cumsum()

    hist = []
    
    # 5. Processa dia a dia
    for data in datas:
        neg_ate = df_neg[df_neg['Data do Negócio'] <= data]
        
        capital_investido = neg_ate['Valor_Sinal'].sum()
        
        pos = neg_ate.groupby('Ticker')['Qtd_Sinal'].sum()

        v_mkt = 0.0
        for t, qtd in pos.items():
            ticker_sa = f"{t}.SA"
            if qtd > 0 and ticker_sa in dados_mkt.columns:
                preco = dados_mkt.loc[data, ticker_sa]
                if not pd.isna(preco):
                    v_mkt += qtd * preco

        hist.append({
            'Data': data,
            'Capital Investido': capital_investido,
            'Valor de Mercado': v_mkt,
            'Proventos Acumulados': proventos_acumulados_serie.loc[data]
        })

    df_h = pd.DataFrame(hist)
    df_h['Data'] = pd.to_datetime(df_h['Data'])
    
    if df_h['Data'].dt.tz is not None:
        df_h['Data'] = df_h['Data'].dt.tz_localize(None)
        
    return df_h

def plotar_grafico_patrimonio(arquivo_carteira):
    st.markdown("---") 
    st.subheader("Evolução: Valor de Mercado x Capital Investido x Proventos")
    
    with st.spinner('Calculando a evolução do patrimônio e proventos...'):
        df_hist = calcular_evolucao_patrimonio(arquivo_carteira)

    col_data1, col_data2, _ = st.columns([1, 1, 2])
    data_min_hist = df_hist['Data'].min().date()
    data_max_hist = df_hist['Data'].max().date()
    
    with col_data1:
        data_inicio = st.date_input("Data Inicial", value=data_min_hist, min_value=data_min_hist, max_value=data_max_hist, key="dt_ini_patrimonio")
    with col_data2:
        data_fim = st.date_input("Data Final", value=data_max_hist, min_value=data_min_hist, max_value=data_max_hist, key="dt_fim_patrimonio")
        
    mask = (df_hist['Data'].dt.date >= data_inicio) & (df_hist['Data'].dt.date <= data_fim)
    df_filt = df_hist.loc[mask].copy()
    
    if not df_filt.empty:
        # Re-basa o Provento Acumulado para zerar na data inicial do filtro (opcional para manter a consistência do recorte)
        provento_inicial_filtro = df_filt['Proventos Acumulados'].iloc[0]
        df_filt['Proventos Acumulados'] = df_filt['Proventos Acumulados'] - provento_inicial_filtro

        fig = go.Figure()

        # 1. Linha do Capital Investido (Azul + Área Sombreada)
        fig.add_trace(go.Scatter(
            x=df_filt['Data'], 
            y=df_filt['Capital Investido'],
            name='Capital Investido',
            mode='lines',
            line=dict(color='#1f77b4', width=2),
            fill='tozeroy',
            fillcolor='rgba(31, 119, 180, 0.15)',
            hovertemplate='R$ %{y:,.2f}'
        ))

        # 2. Linha do Valor de Mercado (Verde)
        fig.add_trace(go.Scatter(
            x=df_filt['Data'], 
            y=df_filt['Valor de Mercado'],
            name='Valor de Mercado',
            mode='lines',
            line=dict(color='#0a9d3b', width=3),
            hovertemplate='R$ %{y:,.2f}'
        ))
        
        # 3. Linha do Valor de Mercado + Proventos (Laranja)
        fig.add_trace(go.Scatter(
            x=df_filt['Data'], 
            # A mágica acontece aqui: somamos as duas colunas
            y=df_filt['Valor de Mercado'] + df_filt['Proventos Acumulados'], 
            name='V. Mercado + Prov.',
            mode='lines',
            line=dict(color='#ff7f0e', width=2),
            hovertemplate='R$ %{y:,.2f}'
        ))
        
        fig.update_layout(
            hovermode="x unified",
            separators=",.",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis_tickprefix="R$ "
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Não há dados no período selecionado.")