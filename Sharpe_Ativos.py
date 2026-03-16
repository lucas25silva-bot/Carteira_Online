import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

@st.cache_data(show_spinner=False, ttl=3600)
def processar_sharpe_ativos(arquivo_carteira):
    def limpar_moeda(valor):
        if pd.isna(valor): return 0.0
        if isinstance(valor, str):
            valor = valor.replace('R$', '').replace('.', '').replace(',', '.')
        try:
            return float(valor)
        except:
            return 0.0

    df_neg = pd.read_excel(arquivo_carteira, sheet_name='Negociação')
    df_neg['Data do Negócio'] = pd.to_datetime(df_neg['Data do Negócio'], dayfirst=True)
    df_neg['Ticker'] = df_neg['Código de Negociação'].str.replace('F$', '', regex=True)
    df_neg['Quantidade'] = pd.to_numeric(df_neg['Quantidade'], errors='coerce').fillna(0)
    
    df_neg['Qtd_Sinal'] = np.where(
        df_neg['Tipo de Movimentação'].str.upper().str.contains('COMPRA'),
        df_neg['Quantidade'], -df_neg['Quantidade']
    )
    
    # Processa Proventos para emular o "div_acum" do código original
    df_prov = pd.DataFrame()
    try:
        df_prov_raw = pd.read_excel(arquivo_carteira, sheet_name='Proventos Recebidos')
        if not df_prov_raw.empty:
            col_data = [c for c in df_prov_raw.columns if 'Pagamento' in c or 'Data' in c][0]
            col_valor = [c for c in df_prov_raw.columns if 'Valor' in c][0]
            
            df_prov = df_prov_raw.copy()
            df_prov['Data'] = pd.to_datetime(df_prov[col_data], dayfirst=True)
            df_prov['Valor_Real'] = df_prov[col_valor].apply(limpar_moeda)
    except:
        pass

    # Monta a matriz de posições diárias
    trades_pivot = df_neg.pivot_table(index='Data do Negócio', columns='Ticker', values='Qtd_Sinal', aggfunc='sum').fillna(0)
    
    data_ini = df_neg['Data do Negócio'].min()
    data_fim = datetime.today()
    datas = pd.date_range(start=data_ini, end=data_fim, freq='B')
    
    posicoes_diarias = trades_pivot.reindex(datas).fillna(0).cumsum()
    ativos_ativos = [t for t in posicoes_diarias.columns if posicoes_diarias[t].iloc[-1] > 0]
    
    if not ativos_ativos:
        return pd.DataFrame()
        
    tickers_yf = [f"{t}.SA" for t in ativos_ativos]
    
    # Puxa o histórico COMPLETO (igual ao código original)
    try:
        dados_raw = yf.download(tickers_yf, start=data_ini - timedelta(days=5), end=data_fim + timedelta(days=1), progress=False)
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
    dados_mkt = dados_mkt.reindex(datas).ffill()
    
    # Alinha as matrizes
    cols_comuns = posicoes_diarias.columns.intersection(dados_mkt.columns)
    posicoes_diarias = posicoes_diarias[cols_comuns]
    dados_mkt = dados_mkt[cols_comuns]
    
    # Valor de Mercado diário
    valor_diario = (posicoes_diarias * dados_mkt).fillna(0)
    valor_diario[valor_diario < 0] = 0 
    v_mkt_diario = valor_diario.sum(axis=1)
    
    # Calcula os Dividendos Acumulados diários
    div_acum_diario = pd.Series(0.0, index=datas)
    if not df_prov.empty:
        for data in datas:
            div_acum_diario[data] = df_prov.loc[df_prov['Data'] <= data, 'Valor_Real'].sum()
            
    # Cria a variável Valor_Total exata do script original
    valor_total_diario = v_mkt_diario + div_acum_diario
    
    # Retorno diário da carteira (usando a variação absoluta do capital)
    ret_carteira = valor_total_diario.replace(0, np.nan).pct_change().dropna()
    
    # Retornos diários dos ativos
    rets_ativos = dados_mkt.pct_change().dropna(how='all')
    
    # Taxa Livre de Risco (10.5% a.a.)
    rf_diario = (1 + 0.105) ** (1/252) - 1
    
    sharpes = []
    
    # 1. Sharpe dos Ativos Individuais (Todo o histórico)
    for t in cols_comuns:
        serie = rets_ativos[t].dropna()
        if len(serie) >= 30:
            ret_medio = serie.mean()
            vol = serie.std()
            
            if vol > 0:
                sharpe_anual = ((ret_medio - rf_diario) / vol) * np.sqrt(252)
                sharpes.append({'Ativo': t, 'Sharpe': sharpe_anual})
                
    # 2. Sharpe da Carteira Global (Matemática idêntica ao código original)
    if len(ret_carteira) >= 30:
        ret_medio_cart = ret_carteira.mean()
        vol_cart = ret_carteira.std()
        
        if vol_cart > 0:
            sharpe_cart_anual = ((ret_medio_cart - rf_diario) / vol_cart) * np.sqrt(252)
            sharpes.append({'Ativo': 'Carteira', 'Sharpe': sharpe_cart_anual})
            
    if sharpes:
        df_sharpe = pd.DataFrame(sharpes).sort_values('Sharpe', ascending=True).reset_index(drop=True)
        return df_sharpe
        
    return pd.DataFrame()

def plotar_sharpe_ativos(arquivo_carteira):
    st.markdown("---")
    st.subheader("Índice Sharpe (Retorno vs. Risco)")
    
    with st.spinner("Calculando a relação Risco-Retorno pelo histórico de patrimônio..."):
        df_sharpe = processar_sharpe_ativos(arquivo_carteira)
        
    if not df_sharpe.empty:
        COR_CARTEIRA = '#002244'  
        COR_POSITIVO = '#0a9d3b'  
        COR_NEGATIVO = '#c62828'  
        
        cores_sharpe = []
        cores_texto = []
        
        for ativo, sharpe in zip(df_sharpe['Ativo'], df_sharpe['Sharpe']):
            if ativo == 'Carteira':
                cores_sharpe.append(COR_CARTEIRA)
                cores_texto.append("white") # Fonte fixada em branco
            elif sharpe >= 0:
                cores_sharpe.append(COR_POSITIVO)
                cores_texto.append(COR_POSITIVO) 
            else:
                cores_sharpe.append(COR_NEGATIVO)
                cores_texto.append(COR_NEGATIVO) 
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df_sharpe['Ativo'],
            y=df_sharpe['Sharpe'],
            marker_color=cores_sharpe,
            text=[f"{s:.2f}" for s in df_sharpe['Sharpe']],
            textposition='outside',
            textfont=dict(color=cores_texto, weight='bold'),
            hovertemplate="<b>%{x}</b><br>Sharpe Ratio: %{y:.2f}<extra></extra>"
        ))
        
        fig.add_shape(
            type="line",
            x0=-0.5,
            y0=0,
            x1=len(df_sharpe)-0.5,
            y1=0,
            line=dict(color="black", width=1.5),
            opacity=0.7
        )
        
        fig.update_layout(
            xaxis_title="",
            yaxis_title="<b>Sharpe Anualizado</b>",
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
        st.warning("Não há dados suficientes para calcular o Índice Sharpe dos ativos.")