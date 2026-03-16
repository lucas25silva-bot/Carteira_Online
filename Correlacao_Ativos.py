import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
from datetime import datetime, timedelta

@st.cache_data(show_spinner=False, ttl=3600)
def processar_correlacao(arquivo_carteira):
    df_neg = pd.read_excel(arquivo_carteira, sheet_name='Negociação')
    df_neg['Ticker'] = df_neg['Código de Negociação'].str.replace('F$', '', regex=True)
    df_neg['Quantidade'] = pd.to_numeric(df_neg['Quantidade'], errors='coerce').fillna(0)
    
    df_neg['Qtd_Sinal'] = np.where(
        df_neg['Tipo de Movimentação'].str.upper().str.contains('COMPRA'),
        df_neg['Quantidade'], -df_neg['Quantidade']
    )
    
    posicao = df_neg.groupby('Ticker')['Qtd_Sinal'].sum()
    ativos_ativos = posicao[posicao > 0].index.tolist()
    
    if len(ativos_ativos) < 2:
        return pd.DataFrame()
        
    tickers_yf = [f"{t}.SA" for t in ativos_ativos] + ['^BVSP']
    
    try:
        dados_raw = yf.download(tickers_yf, period="1y", progress=False)
        if isinstance(dados_raw.columns, pd.MultiIndex):
            dados_mkt = dados_raw['Close'] if 'Close' in dados_raw.columns.get_level_values(0) else dados_raw
        elif 'Close' in dados_raw.columns:
            dados_mkt = dados_raw[['Close']].rename(columns={'Close': tickers_yf[0]}) if len(tickers_yf) == 1 else dados_raw
        else:
            dados_mkt = dados_raw
    except:
        return pd.DataFrame()
        
    if dados_mkt.empty:
        return pd.DataFrame()
        
    if dados_mkt.index.tz is not None:
        dados_mkt.index = dados_mkt.index.tz_localize(None)
        
    dados_mkt.columns = [str(c).replace('.SA', '').replace('^BVSP', 'IBOV') for c in dados_mkt.columns]
    
    # Calcula os retornos diários e a matriz de correlação cruzada
    rets = dados_mkt.pct_change().dropna(how='all')
    corr_matrix = rets.corr().round(2)
    
    return corr_matrix

def plotar_matriz_correlacao(arquivo_carteira):
    st.markdown("---")
    st.subheader("Matriz de Correlação dos Ativos")
    
    with st.spinner("Calculando como os ativos se comportam uns em relação aos outros..."):
        corr_matrix = processar_correlacao(arquivo_carteira)
        
    if not corr_matrix.empty:
        # Cria um Heatmap usando a paleta RdBu (Vermelho para negativo, Azul para positivo)
        fig = px.imshow(
            corr_matrix,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="RdBu",
            zmin=-1, zmax=1,
            labels=dict(color="Correlação")
        )
        
        fig.update_traces(
            hovertemplate="Ativo 1: %{x}<br>Ativo 2: %{y}<br>Correlação: <b>%{z}</b><extra></extra>"
        )
        
        fig.update_layout(
            height=max(400, len(corr_matrix.columns) * 35), # Cresce dinamicamente se houver muitos ativos
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(tickangle=-45, side="bottom")
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Não há ativos suficientes na carteira para montar uma matriz de correlação.")