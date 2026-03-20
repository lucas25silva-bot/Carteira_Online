import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

@st.cache_data(show_spinner=False, ttl=3600)
def listar_todos_ativos(arquivo_carteira, arquivo_ibov):
    ativos = set()
    
    try:
        df_neg = pd.read_excel(arquivo_carteira, sheet_name='Negociação')
        tickers_carteira = df_neg['Código de Negociação'].str.replace('F$', '', regex=True).unique()
        ativos.update(tickers_carteira)
    except:
        pass
        
    try:
        df_ibov = pd.read_csv(arquivo_ibov, sep=';', encoding='latin1', skiprows=1)
        col_codigo = [c for c in df_ibov.columns if 'Cód' in c or 'Cod' in c or 'Ticker' in c]
        if col_codigo:
            tickers_ibov = df_ibov[col_codigo[0]].dropna().unique()
            ativos.update(tickers_ibov)
    except:
        pass
        
    return sorted(list(ativos))

@st.cache_data(show_spinner=False, ttl=3600)
def calcular_pm_historico(arquivo_carteira, ticker):
    try:
        df_neg = pd.read_excel(arquivo_carteira, sheet_name='Negociação')
        df_neg['Data do Negócio'] = pd.to_datetime(df_neg['Data do Negócio'], dayfirst=True)
        df_neg['Ticker'] = df_neg['Código de Negociação'].str.replace('F$', '', regex=True)
        
        def limpar_moeda(v):
            if pd.isna(v): return 0.0
            if isinstance(v, str): v = v.replace('R$', '').replace('.', '').replace(',', '.')
            try: return float(v)
            except: return 0.0

        df_neg['Valor'] = df_neg['Valor'].apply(limpar_moeda)
        df_neg['Quantidade'] = pd.to_numeric(df_neg['Quantidade'], errors='coerce').fillna(0)
        
        df_ativo = df_neg[df_neg['Ticker'] == ticker].sort_values('Data do Negócio').copy()
        
        if df_ativo.empty:
            return pd.DataFrame()
            
        historico_pm = []
        qtd_acumulada = 0
        custo_acumulado = 0.0
        pm_atual = np.nan
        
        for index, row in df_ativo.iterrows():
            data = row['Data do Negócio']
            qtd = row['Quantidade']
            valor = row['Valor']
            tipo = str(row['Tipo de Movimentação']).upper()
            
            if 'COMPRA' in tipo:
                qtd_acumulada += qtd
                custo_acumulado += valor
                if qtd_acumulada > 0:
                    pm_atual = custo_acumulado / qtd_acumulada
            elif 'VENDA' in tipo:
                qtd_acumulada -= qtd
                if not pd.isna(pm_atual):
                    custo_acumulado -= (qtd * pm_atual)
                if qtd_acumulada <= 0:
                    qtd_acumulada = 0
                    custo_acumulado = 0.0
                    pm_atual = np.nan 
                    
            historico_pm.append({'Data': data, 'PM': pm_atual, 'Qtd': qtd_acumulada})
            
        df_pm = pd.DataFrame(historico_pm)
        df_pm = df_pm.groupby('Data').last().reset_index() 
        return df_pm
    except:
        return pd.DataFrame()

def plotar_cotacao_ativos(arquivo_carteira, arquivo_ibov):
    st.markdown("---")
    st.subheader("Cotação Histórica dos Ativos")
    
    lista_ativos = listar_todos_ativos(arquivo_carteira, arquivo_ibov)
    
    # --- FILTROS ---
    col_filtro, col_periodo = st.columns([1, 2])
    
    with col_filtro:
        ativo_selecionado = st.selectbox(
            "Selecione o Ativo:", 
            options=[""] + lista_ativos,
            index=0,
            format_func=lambda x: "Selecione um ativo..." if x == "" else x
        )
        
    with col_periodo:
        periodo_selecionado = st.radio(
            "Período:",
            options=["1M", "3M", "6M", "1A", "2A", "5A", "Máx"],
            index=3, # Padrão: 1 Ano
            horizontal=True
        )
        
    if ativo_selecionado == "":
        st.info("Selecione um ativo no filtro acima para visualizar o gráfico de cotação.")
        return
        
    # --- LÓGICA DE DATAS ---
    hoje = datetime.today()
    if periodo_selecionado == "1M": data_ini = hoje - timedelta(days=30)
    elif periodo_selecionado == "3M": data_ini = hoje - timedelta(days=90)
    elif periodo_selecionado == "6M": data_ini = hoje - timedelta(days=180)
    elif periodo_selecionado == "1A": data_ini = hoje - timedelta(days=365)
    elif periodo_selecionado == "2A": data_ini = hoje - timedelta(days=730)
    elif periodo_selecionado == "5A": data_ini = hoje - timedelta(days=1825)
    else: data_ini = hoje - timedelta(days=3650) # Máx = 10 anos
        
    data_fim = hoje
        
    with st.spinner(f"Buscando cotações de {ativo_selecionado}..."):
        ticker_yf = f"{ativo_selecionado}.SA"
        try:
            # Baixa a cotação
            dados_mkt = yf.download(ticker_yf, start=data_ini, end=data_fim + timedelta(days=1), progress=False)
            if dados_mkt.empty:
                st.warning(f"Não foram encontradas cotações para o ativo {ativo_selecionado} no período selecionado.")
                return
                
            if isinstance(dados_mkt.columns, pd.MultiIndex):
                serie_cotacao = dados_mkt['Close'][ticker_yf]
            else:
                serie_cotacao = dados_mkt['Close']
                
            df_plot = serie_cotacao.reset_index()
            df_plot.columns = ['Data', 'Cotação']
            
            if df_plot['Data'].dt.tz is not None:
                df_plot['Data'] = df_plot['Data'].dt.tz_localize(None)
                
            # --- CÁLCULO E ALINHAMENTO DO PM ---
            df_pm = calcular_pm_historico(arquivo_carteira, ativo_selecionado)
            
            if not df_pm.empty:
                # Cria uma base contínua de dias úteis baseada nas cotações
                datas_cotacao = df_plot[['Data']].copy()
                
                # O merge_asof traz o último PM válido para cada dia de cotação
                df_plot = pd.merge_asof(datas_cotacao, df_pm, on='Data', direction='backward')
                
                # Se o ativo foi comprado ANTES da data de início do gráfico, 
                # forçamos o primeiro PM conhecido para a data inicial
                pm_anterior = df_pm[df_pm['Data'] <= data_ini]
                if not pm_anterior.empty and pd.isna(df_plot['PM'].iloc[0]):
                    pm_vigente = pm_anterior['PM'].iloc[-1]
                    # Preenche os NaNs iniciais com o PM vigente antes do recorte
                    df_plot['PM'] = df_plot['PM'].fillna(pm_vigente)

                # Volta a juntar com a cotação
                df_plot['Cotação'] = serie_cotacao.values
            else:
                df_plot['PM'] = np.nan

            # --- PLOTAGEM DO GRÁFICO ---
            fig = go.Figure()

            # 1. Linha da Cotação (Azul com degradê)
            fig.add_trace(go.Scatter(
                x=df_plot['Data'],
                y=df_plot['Cotação'],
                name=f'Cotação {ativo_selecionado}',
                mode='lines',
                line=dict(color='#1E88E5', width=2),
                fill='tozeroy',
                fillcolor='rgba(30, 136, 229, 0.15)',
                hovertemplate='R$ %{y:.2f}'
            ))

            # 2. Linha do Preço Médio (Laranja tracejado)
            if 'PM' in df_plot.columns and not df_plot['PM'].isna().all():
                fig.add_trace(go.Scatter(
                    x=df_plot['Data'],
                    y=df_plot['PM'],
                    name='Seu Preço Médio',
                    mode='lines',
                    line=dict(color='#FC9149', width=2, dash='dash'),
                    hovertemplate='R$ %{y:.2f}'
                ))

            fig.update_layout(
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                yaxis_tickprefix="R$ ",
                margin=dict(l=20, r=20, t=40, b=20),
                height=450,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )

            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Ocorreu um erro ao carregar o gráfico: {e}")