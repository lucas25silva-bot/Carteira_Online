import pandas as pd
import streamlit as st
import numpy as np

from tabela_score import carregar_dados_em_cache
from tabela_target import carregar_dados_target_cache
from tabela_retornos import carregar_dados_retornos

def plotar_tabela_ranking(posicao, arquivo_ibov):
    st.subheader("Ranking Geral Unificado (Top Ações)")
    
    tickers_carteira = posicao["Ticker"].dropna().unique().tolist()
    tickers_tuple = tuple(tickers_carteira)
    
    with st.spinner("Consolidando dados de todos os módulos para o Ranking Final..."):
        try:
            df_score = carregar_dados_em_cache(tickers_tuple, arquivo_ibov)
            df_target = carregar_dados_target_cache(tickers_tuple, arquivo_ibov)
            
            # ATENÇÃO: Aqui está a correção. Puxando apenas 1 variável!
            df_retornos = carregar_dados_retornos(tickers_tuple, arquivo_ibov) 
            
        except Exception as e:
            st.error(f"Erro ao carregar dados base. Verifique se as outras tabelas carregaram corretamente. Detalhe: {e}")
            return
            
        rank_score = df_score[['Ativo', 'Score Múltiplo']].rename(columns={'Score Múltiplo': 'Nota Múltiplos'})
        rank_target = df_target[['Ativo', 'Nota Upside']]
        rank_retornos = df_retornos[['Ativo', 'Setor', 'Nota Retorno']]
        
        df_rank = rank_retornos.merge(rank_score, on='Ativo', how='outer')
        df_rank = df_rank.merge(rank_target, on='Ativo', how='outer')
        
        df_rank = df_rank[df_rank['Ativo'] != 'IBOVESPA']
        
        df_rank['Nota Múltiplos'] = df_rank['Nota Múltiplos'].fillna(0)
        df_rank['Nota Upside'] = df_rank['Nota Upside'].fillna(0)
        df_rank['Nota Retorno'] = df_rank['Nota Retorno'].fillna(0)

        # ======================================================================
        # PESOS DO RANKING GERAL (ALTERE AQUI A IMPORTÂNCIA DE CADA NOTA)
        # ======================================================================
        PESO_MULTIPLOS = 3.0  
        PESO_UPSIDE = 1.0     
        PESO_RETORNO = 2.0    
        # ======================================================================
        
        soma_pesos = PESO_MULTIPLOS + PESO_UPSIDE + PESO_RETORNO
        
        df_rank['Score Final'] = (
            (df_rank['Nota Múltiplos'] * PESO_MULTIPLOS) +
            (df_rank['Nota Upside'] * PESO_UPSIDE) +
            (df_rank['Nota Retorno'] * PESO_RETORNO)
        ) / soma_pesos

        df_rank = df_rank.sort_values(by='Score Final', ascending=False)
        df_rank['Setor'] = df_rank['Setor'].fillna("Outros")

    col1, col2 = st.columns(2)
    opcoes_setores = sorted([s for s in df_rank["Setor"].unique() if pd.notna(s) and s != 'Índice'])
    opcoes_ativos = sorted([a for a in df_rank["Ativo"].unique() if pd.notna(a)])

    with col1:
        filtro_setor = st.multiselect("Filtrar Ranking por Setor:", options=opcoes_setores, placeholder="Todos os setores...")
    with col2:
        filtro_ativo = st.multiselect("Filtrar Ranking por Ativo:", options=opcoes_ativos, placeholder="Todos os ativos...")

    df_filtrado = df_rank.copy()
    if filtro_setor:
        df_filtrado = df_filtrado[df_filtrado["Setor"].isin(filtro_setor)]
    if filtro_ativo:
        df_filtrado = df_filtrado[df_filtrado["Ativo"].isin(filtro_ativo)]

    def aplicar_estilos(row):
        estilos = [''] * len(row)
        is_carteira = row['Ativo'] in tickers_carteira
        
        for i in range(len(row)):
            if is_carteira:
                estilos[i] = 'background-color: #059669; color: white; font-weight: bold'
        return estilos

    df_styled = df_filtrado.style.apply(aplicar_estilos, axis=1)

    st.dataframe(
        df_styled,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Ativo": st.column_config.TextColumn("Ativo"),
            "Setor": st.column_config.TextColumn("Setor"),
            "Nota Múltiplos": st.column_config.ProgressColumn(
                "Nota Múltiplos", format="%.2f", min_value=0, max_value=10
            ),
            "Nota Upside": st.column_config.ProgressColumn(
                "Nota Upside", format="%.2f", min_value=0, max_value=10
            ),
            "Nota Retorno": st.column_config.ProgressColumn(
                "Nota Retorno", format="%.2f", min_value=0, max_value=10
            ),
            "Score Final": st.column_config.ProgressColumn(
                "👑 SCORE GERAL", format="%.2f", min_value=0, max_value=10
            ),
        }
    )