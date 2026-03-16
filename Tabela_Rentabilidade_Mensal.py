import streamlit as st
import pandas as pd
import numpy as np
from Rentabilidade_Acumulada import processar_dados_twr

def plotar_tabela_mensal(arquivo_carteira):
    st.markdown("---")
    st.subheader("Tabela de Rentabilidade Mensal (%)")
    
    with st.spinner('Calculando rentabilidades mensais...'):
        # Puxa o histórico diário da carteira já calculado (usando o cache para ser instantâneo)
        df = processar_dados_twr(arquivo_carteira).copy()

    # 1. Converte rentabilidades acumuladas em Fatores (Base 1.0)
    df['Fator_Cart'] = 1 + (df['Carteira'] / 100)
    
    ibov_ini = df['IBOV_idx'].dropna().iloc[0] if not df['IBOV_idx'].dropna().empty else 1
    sp500_ini = df['SP500_idx'].dropna().iloc[0] if not df['SP500_idx'].dropna().empty else 1
    
    df['Fator_IBOV'] = df['IBOV_idx'] / ibov_ini
    df['Fator_SP500'] = df['SP500_idx'] / sp500_ini
    df['Fator_CDI'] = 1 + (df['CDI'] / 100)
    df['Fator_IPCA'] = 1 + (df['IPCA + 6%'] / 100)
    
    # 2. Extrai Ano e Mês e agrupa pelo último dia com dados no mês
    df['Ano'] = df['Data'].dt.year
    df['Mes'] = df['Data'].dt.month
    df_mes = df.groupby(['Ano', 'Mes']).last().reset_index()
    
    colunas_fatores = ['Fator_Cart', 'Fator_IBOV', 'Fator_CDI', 'Fator_SP500', 'Fator_IPCA']
    
    # 3. Calcula a variação percentual mês a mês
    for col in colunas_fatores:
        df_mes[f'Ret_{col}'] = df_mes[col].pct_change()
        # Corrige o primeiro mês para comparar com a estaca zero (Fator 1.0)
        df_mes.loc[0, f'Ret_{col}'] = df_mes[col].iloc[0] - 1.0

    meses_map = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 
                 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
                 
    mapa_nomes = {
        'Fator_Cart': 'Carteira',
        'Fator_IBOV': 'IBOV',
        'Fator_CDI': 'CDI',
        'Fator_SP500': 'S&P 500 (BRL)',
        'Fator_IPCA': 'IPCA + 6%'
    }
    
    linhas = []
    
    # 4. Estrutura os dados no formato da matriz Ano/Mês
    for ano in sorted(df_mes['Ano'].unique()):
        df_ano = df_mes[df_mes['Ano'] == ano]
        first_row_ano = True
        
        for col_fator, nome_exibicao in mapa_nomes.items():
            # O TRUQUE DO AGRUPAMENTO: O ano só é escrito na primeira linha!
            linha = {'Ano': str(ano) if first_row_ano else "", 'Índice': nome_exibicao}
            first_row_ano = False
            
            fator_acum_ano = 1.0
            
            for mes_num in range(1, 13):
                mes_nome = meses_map[mes_num]
                valor_mes = df_ano[df_ano['Mes'] == mes_num][f'Ret_{col_fator}']
                
                if not valor_mes.empty and pd.notna(valor_mes.iloc[0]):
                    ret = float(valor_mes.iloc[0])
                    linha[mes_nome] = ret
                    fator_acum_ano *= (1 + ret)
                else:
                    linha[mes_nome] = np.nan
            
            if any(pd.notna(linha[m]) for m in meses_map.values()):
                linha['Acum.'] = fator_acum_ano - 1
            else:
                linha['Acum.'] = np.nan
                
            linhas.append(linha)
            
    df_final = pd.DataFrame(linhas)
    
    # 5. Formatação Visual (Cores e Percentuais)
    def formatar_pct(val):
        if pd.isna(val) or val == "": return "-"
        return f"{val * 100:.2f}%"
        
    def estilizar_tabela(row):
        indice = row['Índice']
        mapa_cores = {
            'Carteira': '#2ECC71', 
            'IBOV': '#1E88E5',
            'S&P 500 (BRL)': '#d1661b',
            'CDI': '#9467BD',
            'IPCA + 6%': '#FBC02D'
        }
        
        estilos = []
        for col, val in row.items():
            if col == 'Ano':
                # Deixa o ano em negrito para destacar a quebra visual
                estilos.append('font-weight: bold; font-size: 14px;') 
            elif col == 'Índice':
                # Pinta o NOME do índice com a mesma cor da linha do gráfico
                cor = mapa_cores.get(val, 'gray')
                estilos.append(f'color: {cor}; font-weight: bold;')
            else:
                # Colunas de Meses e Acumulado
                if pd.isna(val) or isinstance(val, str):
                    estilos.append('')
                elif indice == 'Carteira':
                    if val > 0: estilos.append('color: #0a9d3b; font-weight: bold;')
                    elif val < 0: estilos.append('color: #c62828; font-weight: bold;')
                    else: estilos.append('color: gray; font-weight: bold;')
                else:
                    cor = mapa_cores.get(indice, 'gray')
                    estilos.append(f'color: {cor}; font-weight: bold;')
                    
        return estilos

    cols_meses = list(meses_map.values()) + ['Acum.']
    estilo = df_final.style.format({c: formatar_pct for c in cols_meses})
    
    # Aplica a regra de cores para TODA a tabela de uma vez
    estilo = estilo.apply(estilizar_tabela, axis=1)
        
    # Esconde o índice numérico padrão do Pandas para ficar limpo (hide_index=True)
    st.dataframe(estilo, use_container_width=True, hide_index=True)