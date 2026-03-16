import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

@st.cache_data(show_spinner=False, ttl=3600)
def processar_contribuicao_absoluta(arquivo_carteira):
    def limpar_moeda(valor):
        if pd.isna(valor): return 0.0
        if isinstance(valor, str):
            valor = valor.replace('R$', '').replace('.', '').replace(',', '.')
        try:
            return float(valor)
        except:
            return 0.0

    df_neg = pd.read_excel(arquivo_carteira, sheet_name='Negociação')
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

        if t not in carteira:
            carteira[t] = {'qtd': 0.0, 'pm': 0.0, 'compras': 0.0, 'vendas': 0.0}

        estado = carteira[t]
        if 'COMPRA' in tipo:
            qtd_atual = estado['qtd']
            pm_atual = estado['pm']
            novo_pm = ((qtd_atual * pm_atual) + valor) / (qtd_atual + qtd) if (qtd_atual + qtd) > 0 else 0
            
            estado['qtd'] += qtd
            estado['pm'] = novo_pm
            estado['compras'] += valor
            
        elif 'VENDA' in tipo:
            estado['qtd'] -= qtd
            estado['vendas'] += valor
            
            if estado['qtd'] <= 0:
                estado['qtd'] = 0.0
                estado['pm'] = 0.0

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

    # Para performance, o Yahoo Finance só é chamado para os ativos ATUAIS
    ativos_ativos = [t for t, v in carteira.items() if v['qtd'] > 0]
    tickers_yf = [f"{t}.SA" for t in ativos_ativos]
    
    dados_mkt = pd.DataFrame()
    if tickers_yf:
        data_fim = datetime.today()
        data_ini_mkt = data_fim - timedelta(days=5)
        try:
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
        except:
            pass

    custo_total_carteira = sum([v['qtd'] * v['pm'] for v in carteira.values() if v['qtd'] > 0])
    total_compras_geral = sum([v['compras'] for v in carteira.values()])
    
    resultados = []

    for t, estado in carteira.items():
        qtd = estado['qtd']
        pm = estado['pm']
        compras = estado['compras']
        vendas = estado['vendas']
        prov_acumulado = proventos.get(t, 0.0)
        
        if qtd > 0:
            # LÓGICA 1: ATIVOS AINDA NA CARTEIRA
            ticker_sa = f"{t}.SA"
            preco_atual = 0.0
            
            if not dados_mkt.empty and ticker_sa in dados_mkt.columns:
                s_precos = dados_mkt[ticker_sa].dropna()
                if not s_precos.empty:
                    preco_atual = float(s_precos.iloc[-1])
                    
            if preco_atual == 0.0:
                try:
                    preco_atual = float(yf.Ticker(ticker_sa).fast_info.last_price)
                except:
                    preco_atual = pm 

            valor_mercado = qtd * preco_atual
            custo_ativo = qtd * pm
            lucro_absoluto = (valor_mercado + vendas + prov_acumulado) - compras
            
            contribuicao = (lucro_absoluto / custo_total_carteira) * 100 if custo_total_carteira > 0 else 0.0
            peso = (custo_ativo / custo_total_carteira) * 100 if custo_total_carteira > 0 else 0.0
            status = "Atual"
            nome_exibicao = t
            
        else:
            # LÓGICA 2: OPERAÇÕES ENCERRADAS (VENDIDAS TOTALMENTE)
            lucro_absoluto = (0.0 + vendas + prov_acumulado) - compras
            
            contribuicao = (lucro_absoluto / custo_total_carteira) * 100 if custo_total_carteira > 0 else 0.0
            peso = (compras / total_compras_geral) * 100 if total_compras_geral > 0 else 0.0
            status = "Encerrado"
            nome_exibicao = f"{t} (Encerrado)"

        # Filtro de ruído: Se for encerrada e a contribuição for menor que 0.01%, ele esconde para não poluir o gráfico
        if status == "Atual" or abs(contribuicao) >= 0.01:
            resultados.append({
                'Ativo': nome_exibicao,
                'Contribuicao': contribuicao,
                'Peso': peso,
                'Lucro': lucro_absoluto,
                'Status': status
            })

    df_res = pd.DataFrame(resultados)
    if not df_res.empty:
        df_res = df_res.sort_values('Contribuicao', ascending=True) 
    return df_res

def plotar_contribuicao_retorno(arquivo_carteira):
    st.markdown("---")
    st.subheader("Contribuição de Retorno e Peso por Ativo (%)")
    
    with st.spinner("Analisando todas as operações ativas e encerradas..."):
        df_plot = processar_contribuicao_absoluta(arquivo_carteira)
        
    if not df_plot.empty:
        cores = ['#0a9d3b' if val >= 0 else '#c62828' for val in df_plot['Contribuicao']]
        
        # Cria os textos combinados (diferencia "Peso" atual de "Peso Histórico")
        textos_barras = []
        for status, peso, val in zip(df_plot['Status'], df_plot['Peso'], df_plot['Contribuicao']):
            if status == "Atual":
                textos_barras.append(f"Peso: {peso:.1f}%   |   {val:+.2f}%")
            else:
                textos_barras.append(f"Peso Hist.: {peso:.1f}%   |   {val:+.2f}%")
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=df_plot['Ativo'],
            x=df_plot['Contribuicao'],
            orientation='h',
            marker_color=cores,
            text=textos_barras,
            textposition='outside',
            textfont=dict(color=cores, weight='bold'),
            hovertemplate="<b>%{y}</b><br>Contribuição na Carteira: %{x:.2f}%<br>Peso no Capital: %{customdata[0]:.2f}%<br>Resultado Financeiro: R$ %{customdata[1]:,.2f}<extra></extra>",
            customdata=np.column_stack((df_plot['Peso'], df_plot['Lucro']))
        ))
        
        # A altura cresce dinamicamente se você tiver dezenas de operações encerradas
        altura_grafico = max(400, len(df_plot) * 35)
        
        max_val = df_plot['Contribuicao'].max()
        min_val = df_plot['Contribuicao'].min()
        margem_x = (max_val - min_val) * 0.25 if max_val != min_val else 10

        fig.update_layout(
            xaxis_title="<b>Contribuição na Rentabilidade Total (%)</b>",
            yaxis_title="",
            showlegend=False,
            height=altura_grafico,
            margin=dict(l=20, r=40, t=20, b=40),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(
                range=[min_val - margem_x, max_val + margem_x], 
                showgrid=True, gridcolor='rgba(128,128,128,0.2)', 
                zeroline=True, zerolinecolor='gray', zerolinewidth=2
            ),
            yaxis=dict(showgrid=False)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Não há dados para gerar o gráfico de contribuição.")