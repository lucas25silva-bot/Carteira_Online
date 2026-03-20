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

    proventos_por_ativo = {}
    try:
        df_prov = pd.read_excel(arquivo_carteira, sheet_name='Proventos Recebidos')
        if not df_prov.empty:
            col_produto = next((c for c in df_prov.columns if 'Produto' in c or 'Código' in c), None)
            col_valor = next((c for c in df_prov.columns if 'Valor' in c), None)
            
            if col_produto and col_valor:
                df_prov['Ticker_Prov'] = df_prov[col_produto].astype(str).str.split(' - ').str[0].str.strip().str.replace('F$', '', regex=True)
                df_prov['Valor_Real'] = df_prov[col_valor].apply(limpar_moeda)
                proventos_por_ativo = df_prov.groupby('Ticker_Prov')['Valor_Real'].sum().to_dict()
    except:
        pass

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
                qtd_atual += qtd_mov
                valor_acum_compras += valor_mov
                qtd_acum_compras += qtd_mov
            elif 'VENDA' in mov:
                qtd_atual -= qtd_mov
                
        if qtd_acum_compras > 0:
            pm = valor_acum_compras / qtd_acum_compras
        else:
            pm = 0.0
            
        if qtd_atual > 0:
            prov_acum = proventos_por_ativo.get(ticker, 0.0)
            ativos_info.append({
                'Ticker': ticker,
                'Quantidade Atual': qtd_atual,
                'PM (R$)': round(pm, 2),
                'Total Proventos (R$)': prov_acum
            })
            
    return pd.DataFrame(ativos_info)

def buscar_precos_mercado(df_posicao):
    if df_posicao.empty: return df_posicao
    
    tickers = [f"{t}.SA" for t in df_posicao['Ticker']]
    dados = yf.download(tickers, period="5d", progress=False)
    
    precos_atuais = {}
    
    if isinstance(dados.columns, pd.MultiIndex):
        for t in df_posicao['Ticker']:
            ticker_sa = f"{t}.SA"
            if 'Close' in dados.columns.get_level_values(0):
                try: precos_atuais[t] = float(dados['Close'][ticker_sa].dropna().iloc[-1])
                except: precos_atuais[t] = 0.0
    else:
        t = df_posicao['Ticker'].iloc[0]
        try: precos_atuais[t] = float(dados['Close'].dropna().iloc[-1])
        except: precos_atuais[t] = 0.0
        
    df_posicao['Preço Atual (R$)'] = df_posicao['Ticker'].map(precos_atuais)
    df_posicao['Custo Total (R$)'] = df_posicao['Quantidade Atual'] * df_posicao['PM (R$)']
    
    df_posicao['Valor de Mercado (R$)'] = df_posicao['Quantidade Atual'] * df_posicao['Preço Atual (R$)']
    
    # --- NOVO: CÁLCULO DA % NA CARTEIRA ---
    valor_total_carteira = df_posicao['Valor de Mercado (R$)'].sum()
    df_posicao['% na Carteira'] = np.where(
        valor_total_carteira > 0,
        (df_posicao['Valor de Mercado (R$)'] / valor_total_carteira) * 100,
        0
    )
    
    df_posicao['Rentabilidade (%)'] = np.where(
        df_posicao['Custo Total (R$)'] > 0, 
        ((df_posicao['Valor de Mercado (R$)'] / df_posicao['Custo Total (R$)']) - 1) * 100, 
        0
    )
    
    df_posicao['Rentabilidade com Proventos (%)'] = np.where(
        df_posicao['Custo Total (R$)'] > 0, 
        (((df_posicao['Valor de Mercado (R$)'] + df_posicao.get('Total Proventos (R$)', 0)) / df_posicao['Custo Total (R$)']) - 1) * 100, 
        0
    )
    
    # --- NOVO: ORDENAÇÃO PELO MAIOR PESO ---
    df_posicao = df_posicao.sort_values(by='% na Carteira', ascending=False).reset_index(drop=True)
    
    return df_posicao

def gerar_historico_carteira(arquivo_carteira):
    df_neg = pd.read_excel(arquivo_carteira, sheet_name='Negociação')
    df_neg['Data do Negócio'] = pd.to_datetime(df_neg['Data do Negócio'], dayfirst=True)
    df_neg['Ticker'] = df_neg['Código de Negociação'].str.replace('F$', '', regex=True)
    df_neg['Valor'] = df_neg['Valor'].apply(limpar_moeda)

    datas_validas = pd.date_range(start=df_neg['Data do Negócio'].min(), end=pd.Timestamp.today(), freq='B')
    df_custo_total = pd.Series(0.0, index=datas_validas)
    
    tickers = df_neg['Ticker'].unique()
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
        
    rentabilidade_carteira = pd.DataFrame({'Data': datas_validas, 'Aportes Acumulados': df_custo_total}).reset_index(drop=True)
    return rentabilidade_carteira