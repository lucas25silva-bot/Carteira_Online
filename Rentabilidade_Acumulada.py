import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
from datetime import timedelta
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@st.cache_data(show_spinner=False, ttl=3600)
def processar_dados_twr(arquivo_carteira):
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

    df_neg['Valor_Sinal'] = np.where(
        df_neg['Tipo de Movimentação'].str.upper().str.contains('COMPRA'),
        df_neg['Valor'], -df_neg['Valor']
    )
    df_neg['Qtd_Sinal'] = np.where(
        df_neg['Tipo de Movimentação'].str.upper().str.contains('COMPRA'),
        df_neg['Quantidade'], -df_neg['Quantidade']
    )

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
    
    dados_mkt = yf.download(
        tickers + ['^BVSP', '^GSPC', 'USDBRL=X'],
        start=data_ini - timedelta(days=5),
        progress=False
    )['Close']

    # Remove qualquer traço de fuso horário do Yahoo Finance
    if dados_mkt.index.tz is not None:
        dados_mkt.index = dados_mkt.index.tz_localize(None)

    datas = pd.date_range(start=data_ini, end=dados_mkt.index.max(), freq='B')
    dados_mkt = dados_mkt.reindex(datas).ffill()

    hist = []
    valor_inicial = None
    fator_twr = 1.0

    for data in datas:
        fluxo_dia = df_neg.loc[df_neg['Data do Negócio'] == data, 'Valor_Sinal'].sum()
        
        neg_ate = df_neg[df_neg['Data do Negócio'] <= data]
        pos = neg_ate.groupby('Ticker')['Qtd_Sinal'].sum()

        v_mkt = 0.0
        for t, qtd in pos.items():
            ticker_sa = f"{t}.SA"
            if qtd > 0 and ticker_sa in dados_mkt.columns:
                preco = dados_mkt.loc[data, ticker_sa]
                if not pd.isna(preco):
                    v_mkt += qtd * preco

        valor_final = v_mkt
        retorno_dia = 0.0

        if valor_inicial is not None and (valor_inicial + fluxo_dia) != 0:
            retorno_dia = (valor_final - valor_inicial - fluxo_dia + div_por_dia.get(data, 0.0)) / (valor_inicial + fluxo_dia)
            fator_twr *= (1 + retorno_dia)

        rent_acumulada = (fator_twr - 1) * 100

        hist.append({
            'Data': data,
            'Carteira': rent_acumulada,
            'IBOV_idx': dados_mkt.loc[data, '^BVSP'] if '^BVSP' in dados_mkt.columns else np.nan,
            'SP500_idx': dados_mkt.loc[data, '^GSPC'] * dados_mkt.loc[data, 'USDBRL=X'] if '^GSPC' in dados_mkt.columns else np.nan
        })
        valor_inicial = valor_final

    df_h = pd.DataFrame(hist)
    df_h['Data'] = pd.to_datetime(df_h['Data'])
    
    # Remove fuso horário da base principal antes de cruzar com o BCB
    if df_h['Data'].dt.tz is not None:
        df_h['Data'] = df_h['Data'].dt.tz_localize(None)
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    # ==========================================
    # CÁLCULO BLINDADO: CDI
    # ==========================================
    try:
        url_cdi = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados?formato=json&dataInicial={data_ini.strftime('%d/%m/%Y')}"
        resp_cdi = requests.get(url_cdi, headers=headers, timeout=15, verify=False)
        cdi = pd.DataFrame(resp_cdi.json())
        
        if not cdi.empty and 'data' in cdi.columns:
            cdi['data'] = pd.to_datetime(cdi['data'], dayfirst=True)
            cdi['valor'] = pd.to_numeric(cdi['valor'], errors='coerce').fillna(0) / 100
            if cdi['data'].dt.tz is not None:
                cdi['data'] = cdi['data'].dt.tz_localize(None)
            
            # Cruzamento exato dia a dia sem reindex
            cdi = cdi.set_index('data')
            df_h['CDI_diario'] = df_h['Data'].map(cdi['valor']).fillna(0)
            df_h['CDI'] = ((1 + df_h['CDI_diario']).cumprod() - 1) * 100
        else:
            df_h['CDI'] = 0.0
    except Exception as e:
        df_h['CDI'] = 0.0
        st.error(f"⚠️ Erro ao calcular CDI: {e}")

    # ==========================================
    # CÁLCULO BLINDADO: IPCA + 6%
    # ==========================================
    try:
        url_ipca = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json&dataInicial={data_ini.strftime('%d/%m/%Y')}"
        resp_ipca = requests.get(url_ipca, headers=headers, timeout=15, verify=False)
        ipca_raw = pd.DataFrame(resp_ipca.json())
        
        if not ipca_raw.empty and 'data' in ipca_raw.columns:
            ipca_raw['data'] = pd.to_datetime(ipca_raw['data'], dayfirst=True)
            ipca_raw['valor'] = pd.to_numeric(ipca_raw['valor'], errors='coerce').fillna(0) / 100 
            if ipca_raw['data'].dt.tz is not None:
                ipca_raw['data'] = ipca_raw['data'].dt.tz_localize(None)

            taxa_fixa_mes = (1 + 0.06)**(1/12) - 1
            ipca_raw['fator_composto'] = (1 + ipca_raw['valor']) * (1 + taxa_fixa_mes)
            ipca_raw['data_fim'] = ipca_raw['data'] + pd.offsets.MonthEnd(0)
            
            serie_mensal = ipca_raw.set_index('data_fim')['fator_composto'].cumprod()
            data_base_inicial = df_h['Data'].min() - timedelta(days=1)
            s_start = pd.Series([1.0], index=[data_base_inicial])
            serie_completa = pd.concat([s_start, serie_mensal]).sort_index()
            serie_completa = serie_completa[~serie_completa.index.duplicated(keep='last')]
            
            idx_diario = pd.date_range(start=data_base_inicial, end=df_h['Data'].max(), freq='D')
            ipca_diario = serie_completa.reindex(idx_diario).interpolate(method='time')
            
            ipca_final = df_h['Data'].map(ipca_diario).ffill()
            df_h['IPCA + 6%'] = (ipca_final / ipca_final.iloc[0] - 1) * 100
        else:
            df_h['IPCA + 6%'] = 0.0
    except Exception as e:
        df_h['IPCA + 6%'] = 0.0
        st.error(f"⚠️ Erro ao calcular IPCA: {e}")

    return df_h

def plotar_grafico_historico(arquivo_carteira):
    st.markdown("---") 
    st.subheader("Rentabilida Acumulada x Benchmarks")
    
    with st.spinner('Construindo o histórico da carteira e dos benchmarks... (Isso pode levar alguns segundos)'):
        df_hist = processar_dados_twr(arquivo_carteira)

    col_data1, col_data2, _ = st.columns([1, 1, 2])
    data_min_hist = df_hist['Data'].min().date()
    data_max_hist = df_hist['Data'].max().date()
    
    with col_data1:
        data_inicio = st.date_input("Data de Início", value=data_min_hist, min_value=data_min_hist, max_value=data_max_hist)
    with col_data2:
        data_fim = st.date_input("Data de Fim", value=data_max_hist, min_value=data_min_hist, max_value=data_max_hist)
        
    mask = (df_hist['Data'].dt.date >= data_inicio) & (df_hist['Data'].dt.date <= data_fim)
    df_filt = df_hist.loc[mask].copy()
    
    if not df_filt.empty:
        for col in ['Carteira', 'CDI', 'IPCA + 6%']:
            if col in df_filt.columns:
                fator = 1 + (df_filt[col] / 100)
                df_filt[col] = ((fator / fator.iloc[0]) - 1) * 100
        
        for col_idx, col_name in [('IBOV_idx', 'IBOV'), ('SP500_idx', 'S&P 500 (BRL)')]:
            if col_idx in df_filt.columns:
                df_filt[col_name] = ((df_filt[col_idx] / df_filt[col_idx].iloc[0]) - 1) * 100
        
        cols_plot = ['Data', 'Carteira', 'IBOV', 'S&P 500 (BRL)', 'CDI', 'IPCA + 6%']
        df_plot = df_filt[cols_plot].melt(id_vars=['Data'], var_name='Índice', value_name='Rentabilidade Acumulada (%)')
        
        mapa_cores = {
            'Carteira': '#2ECC71', 
            'IBOV': '#1E88E5',
            'S&P 500 (BRL)': '#d1661b',
            'CDI': '#9467BD',
            'IPCA + 6%': '#FBC02D'
        }
        
        fig = px.line(df_plot, x='Data', y='Rentabilidade Acumulada (%)', color='Índice',
                      color_discrete_map=mapa_cores)
        
        fig.update_layout(
            hovermode="x unified",
            legend_title_text="",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig.update_traces(hovertemplate="%{y:.2f}%")
        
        st.plotly_chart(fig, use_container_width=True)
        return df_filt['Carteira'].iloc[-1]
    else:
        st.warning("Não há dados de negociação no período selecionado.")
        return 0.0