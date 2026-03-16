import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

@st.cache_data(show_spinner=False, ttl=3600)
def processar_beta_ativos(arquivo_carteira):
    df_neg = pd.read_excel(arquivo_carteira, sheet_name='Negociação')
    df_neg['Ticker'] = df_neg['Código de Negociação'].str.replace('F$', '', regex=True)
    df_neg['Quantidade'] = pd.to_numeric(df_neg['Quantidade'], errors='coerce').fillna(0)
    
    df_neg['Qtd_Sinal'] = np.where(
        df_neg['Tipo de Movimentação'].str.upper().str.contains('COMPRA'),
        df_neg['Quantidade'], -df_neg['Quantidade']
    )
    
    posicao = df_neg.groupby('Ticker')['Qtd_Sinal'].sum()
    ativos_ativos = posicao[posicao > 0].index.tolist()
    
    if not ativos_ativos:
        return pd.DataFrame()
        
    tickers_yf = [f"{t}.SA" for t in ativos_ativos] + ['^BVSP']
    
    try:
        dados_raw = yf.download(tickers_yf, period="2y", progress=False)
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
        
    dados_mkt.columns = [str(c).replace('.SA', '') for c in dados_mkt.columns]
    
    precos_atuais = dados_mkt.ffill().iloc[-1]
    valor_total_carteira = 0.0
    pesos = {}
    
    for t in ativos_ativos:
        if t in precos_atuais and not pd.isna(precos_atuais[t]):
            valor = posicao[t] * precos_atuais[t]
            pesos[t] = valor
            valor_total_carteira += valor
    
    if valor_total_carteira > 0:
        for t in pesos:
            pesos[t] = pesos[t] / valor_total_carteira
            
    rets = dados_mkt.pct_change()
    
    if '^BVSP' not in rets.columns:
        return pd.DataFrame()
        
    ibov_ret = rets['^BVSP'].dropna()
    betas = []
    beta_carteira = 0.0
    
    for t in ativos_ativos:
        if t in rets.columns:
            serie = rets[t].dropna()
            comum = serie.index.intersection(ibov_ret.index)
            
            if len(comum) > 30:
                cov = np.cov(serie.loc[comum], ibov_ret.loc[comum])[0, 1]
                var_ibov_comum = np.var(ibov_ret.loc[comum])
                
                if var_ibov_comum > 0:
                    beta_ativo = cov / var_ibov_comum
                    betas.append({'Ativo': t, 'Beta': beta_ativo})
                    beta_carteira += beta_ativo * pesos.get(t, 0.0)
            
    if betas:
        betas.append({'Ativo': 'Carteira', 'Beta': beta_carteira})
        df_beta = pd.DataFrame(betas).sort_values('Beta', ascending=True).reset_index(drop=True)
        return df_beta
        
    return pd.DataFrame()

def plotar_beta_ativos(arquivo_carteira):
    st.markdown("---")
    st.subheader("Beta dos Ativos (Sensibilidade ao Mercado)")
    
    with st.spinner("Calculando o grau de volatilidade e risco de cada ativo vs IBOV..."):
        df_beta = processar_beta_ativos(arquivo_carteira)
        
    if not df_beta.empty:
        COR_PRIMARIA = '#002244'
        COR_SECUNDARIA = '#94a3b8'
        
        cores_beta = [
            COR_PRIMARIA if a == 'Carteira' else COR_SECUNDARIA
            for a in df_beta['Ativo']
        ]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df_beta['Ativo'],
            y=df_beta['Beta'],
            marker_color=cores_beta,
            text=[f"{b:.2f}" for b in df_beta['Beta']],
            textposition='outside',
            textfont=dict(weight='bold'),
            hovertemplate="<b>%{x}</b><br>Beta Histórico (2A): %{y:.2f}<extra></extra>"
        ))
        
        fig.add_shape(
            type="line",
            x0=-0.5,
            y0=1,
            x1=len(df_beta)-0.5,
            y1=1,
            line=dict(color="black", width=2, dash="dash"),
            opacity=0.6
        )
        
        fig.add_annotation(
            x=len(df_beta)-1,
            y=1.05,
            text="Beta = 1 (Mercado)",
            showarrow=False,
            font=dict(size=12, color="gray"),
            xanchor='right',
            yanchor='bottom'
        )
        
        fig.update_layout(
            xaxis_title="",
            yaxis_title="<b>Beta em relação ao IBOV</b>",
            showlegend=False,
            height=450,
            margin=dict(l=20, r=20, t=40, b=40),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
            xaxis=dict(tickangle=-45)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Não há dados suficientes para calcular o Beta dos ativos.")