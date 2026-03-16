import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

@st.cache_data(show_spinner=False, ttl=3600)
def processar_risco_retorno(arquivo_carteira):
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
    df_neg['Valor'] = df_neg['Valor'].apply(limpar_moeda)
    df_neg['Quantidade'] = pd.to_numeric(df_neg['Quantidade'], errors='coerce').fillna(0)
    df_neg = df_neg.sort_values('Data do Negócio')

    carteira = {}
    for _, row in df_neg.iterrows():
        t = row['Ticker']
        tipo = str(row['Tipo de Movimentação']).upper()
        qtd = row['Quantidade']
        valor = row['Valor']
        data = row['Data do Negócio']

        if t not in carteira:
            carteira[t] = {'qtd': 0.0, 'pm': 0.0, 'data_ini': None}

        estado = carteira[t]
        if 'COMPRA' in tipo:
            if estado['qtd'] == 0:
                estado['data_ini'] = data
            qtd_atual = estado['qtd']
            pm_atual = estado['pm']
            novo_pm = ((qtd_atual * pm_atual) + valor) / (qtd_atual + qtd) if (qtd_atual + qtd) > 0 else 0
            estado['qtd'] += qtd
            estado['pm'] = novo_pm
        elif 'VENDA' in tipo:
            estado['qtd'] -= qtd
            if estado['qtd'] <= 0:
                estado['qtd'] = 0.0
                estado['pm'] = 0.0
                estado['data_ini'] = None

    ativos_ativos = {t: v for t, v in carteira.items() if v['qtd'] > 0}

    if not ativos_ativos:
        return pd.DataFrame(), 0, 0

    proventos = {}
    try:
        df_prov = pd.read_excel(arquivo_carteira, sheet_name='Proventos Recebidos')
        if not df_prov.empty:
            col_ticker = [c for c in df_prov.columns if 'Código' in c or 'Produto' in c or 'Ativo' in c or 'Ticker' in c][0]
            col_valor = [c for c in df_prov.columns if 'Valor' in c][0]
            df_prov['Ticker'] = df_prov[col_ticker].str.replace('F$', '', regex=True)
            df_prov['Valor_Real'] = df_prov[col_valor].apply(limpar_moeda)
            proventos = df_prov.groupby('Ticker')['Valor_Real'].sum().to_dict()
    except:
        pass

    tickers_yf = [f"{t}.SA" for t in ativos_ativos.keys()] + ['^BVSP']
    data_fim = datetime.today()
    data_ini_mkt = data_fim - timedelta(days=365)

    dados_raw = yf.download(tickers_yf, start=data_ini_mkt, end=data_fim, progress=False)

    if isinstance(dados_raw.columns, pd.MultiIndex):
        dados_mkt = dados_raw['Close'] if 'Close' in dados_raw.columns.get_level_values(0) else dados_raw
    elif 'Close' in dados_raw.columns:
        dados_mkt = dados_raw[['Close']].rename(columns={'Close': tickers_yf[0]}) if len(tickers_yf) == 1 else dados_raw
    else:
        dados_mkt = dados_raw

    if dados_mkt.index.tz is not None:
        dados_mkt.index = dados_mkt.index.tz_localize(None)

    dados_mkt = dados_mkt.ffill()
    retornos_diarios = dados_mkt.pct_change()

    resultados = []
    retorno_ibov = 0.0
    risco_ibov = 0.0

    if '^BVSP' in dados_mkt.columns:
        s_ibov = dados_mkt['^BVSP'].dropna()
        if len(s_ibov) > 30:
            retorno_ibov = ((s_ibov.iloc[-1] / s_ibov.iloc[0]) ** (252 / len(s_ibov)) - 1) * 100
            risco_ibov = retornos_diarios['^BVSP'].dropna().std() * np.sqrt(252) * 100

    for t, estado in ativos_ativos.items():
        ticker_sa = f"{t}.SA"
        if ticker_sa in dados_mkt.columns:
            s_precos = dados_mkt[ticker_sa].dropna()

            if len(s_precos) > 0:
                preco_atual = s_precos.iloc[-1]
                qtd = estado['qtd']
                pm = estado['pm']
                data_compra = estado['data_ini']

                custo_total = qtd * pm
                valor_mercado = qtd * preco_atual
                prov_acumulado = proventos.get(t, 0.0)

                dias_carteira = (data_fim - data_compra).days if data_compra is not None else 1
                if dias_carteira <= 0: dias_carteira = 1

                if custo_total > 0:
                    retorno_total = ((valor_mercado + prov_acumulado) / custo_total) - 1
                    retorno_anualizado = (((1 + retorno_total) ** (1 / (dias_carteira / 252))) - 1) * 100
                else:
                    retorno_anualizado = 0.0

                risco = retornos_diarios[ticker_sa].dropna().std() * np.sqrt(252) * 100

                if not pd.isna(risco) and not pd.isna(retorno_anualizado):
                    resultados.append({
                        'Ativo': t,
                        'Risco': risco,
                        'Retorno': retorno_anualizado,
                        'Tamanho': float(valor_mercado)
                    })

    df_res = pd.DataFrame(resultados)
    return df_res, retorno_ibov, risco_ibov

def plotar_grafico_risco_retorno(arquivo_carteira):
    st.markdown("---")
    st.subheader("Matriz de Risco x Retorno Anualizado (Histórico Completo)")
    
    with st.spinner("Calculando retorno total com proventos e ajustando no tempo..."):
        dados = processar_risco_retorno(arquivo_carteira)
        
    if isinstance(dados, tuple) and not dados[0].empty:
        # Pega os dados dos ativos e ignora o IBOV (os dois underlines "_" servem para ignorar)
        df_plot, _, _ = dados 
        
        df_plot['Tamanho'] = df_plot['Tamanho'].fillna(0)
        tamanho_max = df_plot['Tamanho'].max() if df_plot['Tamanho'].max() > 0 else 1
        df_plot['Tamanho_Plot'] = (df_plot['Tamanho'] / tamanho_max) * 45 + 15
        
        # Define as cores sólidas baseadas em lucro ou prejuízo
        cores = ['#0a9d3b' if ret >= 0 else '#c62828' for ret in df_plot['Retorno']]
        
        fig = go.Figure()

        # Plota as ações
        fig.add_trace(go.Scatter(
            x=df_plot['Risco'],
            y=df_plot['Retorno'],
            mode='markers+text',
            text=df_plot['Ativo'],
            textposition="top center",
            textfont=dict(size=11, color="gray"),
            marker=dict(
                size=df_plot['Tamanho_Plot'],
                color=cores,
                line=dict(width=1.5, color='white'),
                opacity=0.85
            ),
            hovertemplate="<b>%{text}</b><br>Volatilidade: %{x:.2f}%<br>Retorno Anualizado: %{y:.2f}%<extra></extra>"
        ))
        
        # Destaca a Linha do Zero (Linha d'água do Lucro/Prejuízo)
        fig.add_hline(
            y=0, 
            line_width=2, 
            line_color="gray", 
            opacity=0.8,
            annotation_text=" Lucro ↑ / Prejuízo ↓", 
            annotation_position="bottom right",
            annotation_font_color="gray"
        )

        fig.update_layout(
            xaxis_title="<b>Risco / Volatilidade Anualizada (%)</b>",
            yaxis_title="<b>Retorno Anualizado Real (Cotação + Proventos) (%)</b>",
            showlegend=False,
            height=600,
            margin=dict(l=40, r=40, t=50, b=40),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)', zeroline=False),
            yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)', zeroline=False)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Não foi possível gerar o gráfico de risco e retorno.")