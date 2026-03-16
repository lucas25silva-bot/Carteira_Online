import pandas as pd
import numpy as np
import yfinance as yf

def limpar_moeda(valor):
    if pd.isna(valor): return 0.0
    if isinstance(valor, str):
        valor = valor.replace('R$', '').replace('.', '').replace(',', '.')
    try:
        return float(valor)
    except:
        return 0.0

def processar_planilha_carteira(arquivo_carteira):
    df_neg = pd.read_excel(arquivo_carteira, sheet_name='Negociação')
    df_neg['Data do Negócio'] = pd.to_datetime(df_neg['Data do Negócio'], dayfirst=True)
    df_neg['Ticker'] = df_neg['Código de Negociação'].str.replace('F$', '', regex=True)
    df_neg['Valor'] = df_neg['Valor'].apply(limpar_moeda)

    ativos_info = []
    
    for ticker in df_neg['Ticker'].unique():
        neg_ativo = df_neg[df_neg['Ticker'] == ticker].sort_values('Data do Negócio')
        
        valor_acum_compras = 0.0
        qtd_acum_compras = 0
        qtd_atual = 0
        
        for _, row in neg_ativo.iterrows():
            mov = str(row['Tipo de Movimentação']).upper()
            qtd_mov = row['Quantidade']
            valor_mov = row['Valor']
            
            if 'COMPRA' in mov:
                valor_acum_compras += valor_mov
                qtd_acum_compras += qtd_mov
                qtd_atual += qtd_mov
            elif 'VENDA' in mov:
                qtd_atual -= qtd_mov
                if qtd_atual <= 0:
                    qtd_atual = 0
                    valor_acum_compras = 0.0
                    qtd_acum_compras = 0
        
        if qtd_atual > 0:
            pm = valor_acum_compras / qtd_acum_compras if qtd_acum_compras > 0 else 0.0
            custo_total = qtd_atual * pm
            ativos_info.append({
                'Ticker': ticker,
                'Quantidade Atual': qtd_atual,
                'PM (R$)': pm,
                'Custo Total (R$)': custo_total
            })
            
    return pd.DataFrame(ativos_info)

def buscar_precos_mercado(posicao):
    tickers_sa = [f"{t}.SA" for t in posicao['Ticker']]
    tickers_busca = tickers_sa + ['^BVSP']
    
    dados_mkt = yf.download(tickers_busca, period="5d", progress=False)['Close']
    
    precos_atuais = []
    for t in posicao['Ticker']:
        ticker_sa = f"{t}.SA"
        try:
            preco = dados_mkt[ticker_sa].dropna().iloc[-1]
            precos_atuais.append(float(preco))
        except:
            precos_atuais.append(0.0)
            
    posicao['Preço Atual (R$)'] = precos_atuais
    posicao['Valor de Mercado (R$)'] = posicao['Quantidade Atual'] * posicao['Preço Atual (R$)']
    
    valor_total = posicao['Valor de Mercado (R$)'].sum()
    posicao['% na Carteira'] = np.where(valor_total > 0, (posicao['Valor de Mercado (R$)'] / valor_total) * 100, 0.0)
    
    posicao['Rentabilidade (%)'] = np.where(
        posicao['Custo Total (R$)'] > 0,
        ((posicao['Valor de Mercado (R$)'] / posicao['Custo Total (R$)']) - 1) * 100,
        0.0
    )
    
    return posicao.sort_values('Valor de Mercado (R$)', ascending=False).reset_index(drop=True)

# ==========================================
# CÁLCULO DE HISTÓRICO DIÁRIO PARA O GRÁFICO
# ==========================================
def gerar_historico_carteira(arquivo_carteira):
    df_neg = pd.read_excel(arquivo_carteira, sheet_name='Negociação')
    df_neg['Data do Negócio'] = pd.to_datetime(df_neg['Data do Negócio'], dayfirst=True)
    df_neg['Ticker'] = df_neg['Código de Negociação'].str.replace('F$', '', regex=True)
    df_neg['Valor'] = df_neg['Valor'].apply(limpar_moeda)

    data_inicio = df_neg['Data do Negócio'].min()
    data_fim = pd.Timestamp.today()
    
    tickers = df_neg['Ticker'].unique().tolist()
    tickers_sa = [f"{t}.SA" for t in tickers]
    tickers_busca = tickers_sa + ['^BVSP']
    
    dados_mkt = yf.download(tickers_busca, start=data_inicio, end=data_fim, progress=False)['Close']
    if isinstance(dados_mkt, pd.Series): 
        dados_mkt = dados_mkt.to_frame('^BVSP')
        
    dados_mkt.index = pd.to_datetime(dados_mkt.index).tz_localize(None)
    dados_mkt = dados_mkt.ffill().fillna(0)
    datas_validas = dados_mkt.index
    
    mov_diario = df_neg.copy()
    mov_diario['Qtd_Sinal'] = np.where(mov_diario['Tipo de Movimentação'].str.upper().str.contains('COMPRA'), mov_diario['Quantidade'], -mov_diario['Quantidade'])
    
    df_qtd = mov_diario.groupby(['Data do Negócio', 'Ticker'])['Qtd_Sinal'].sum().unstack(fill_value=0)
    df_qtd = df_qtd.reindex(datas_validas, fill_value=0).cumsum()
    
    vm_diario = pd.Series(0.0, index=datas_validas)
    for ticker in tickers:
        ticker_sa = f"{ticker}.SA"
        if ticker_sa in dados_mkt.columns:
            vm_diario += df_qtd[ticker] * dados_mkt[ticker_sa]
            
    df_custo_total = pd.Series(0.0, index=datas_validas)
    for ticker in tickers:
        neg_ativo = df_neg[df_neg['Ticker'] == ticker].sort_values('Data do Negócio')
        custo_serie = []
        neg_idx, n_neg = 0, len(neg_ativo)
        valor_acum, qtd_acum, qtd_atual = 0.0, 0, 0
        
        for dt in datas_validas:
            while neg_idx < n_neg and neg_ativo.iloc[neg_idx]['Data do Negócio'] <= dt:
                row = neg_ativo.iloc[neg_idx]
                m = str(row['Tipo de Movimentação']).upper()
                q, v = row['Quantidade'], row['Valor']
                
                if 'COMPRA' in m:
                    valor_acum += v; qtd_acum += q; qtd_atual += q
                elif 'VENDA' in m:
                    qtd_atual -= q
                    if qtd_atual <= 0:
                        qtd_atual = 0; valor_acum = 0.0; qtd_acum = 0
                neg_idx += 1
                
            if qtd_atual > 0 and qtd_acum > 0:
                pm = valor_acum / qtd_acum
                custo_serie.append(qtd_atual * pm)
            else:
                custo_serie.append(0.0)
                
        df_custo_total += pd.Series(custo_serie, index=datas_validas)
        
    rentabilidade_carteira = np.where(df_custo_total > 0, (vm_diario / df_custo_total - 1) * 100, 0.0)
    
    df_historico = pd.DataFrame({
        'Data': datas_validas,
        'Rentabilidade Carteira (%)': rentabilidade_carteira,
        'IBOV (Pontos)': dados_mkt['^BVSP'].values
    })
    
    return df_historico