import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from Rentabilidade_Acumulada import processar_dados_twr
from Valor_Mercado_Capital import calcular_evolucao_patrimonio
from Sharpe_Ativos import processar_sharpe_ativos
from Beta_Ativos import processar_beta_ativos

def plotar_cards_resumo(posicao, valor_total_carteira, arquivo_carteira):
    st.markdown("### Visão Geral da Carteira")
    
    # ==========================================
    # VARIÁVEIS INICIAIS
    # ==========================================
    rent_mes_atual = 0.0
    label_mes = "Mês Atual"
    rent_str = "-"
    var_str = "-"
    vol_str = "-"
    
    capital_investido = 0.0
    ganho_total = 0.0
    rentab_total = 0.0
    sharpe_total = 0.0
    beta_total = 0.0
    media_retorno_pct = 0.0
    
    cap_inv_str = "-"
    ganho_str = "-"
    rentab_str = "-"
    sharpe_str = "-"
    beta_str = "-"
    media_ret_str = "-"
    
    meses_acima_str = "-"
    meses_abaixo_str = "-"
    
    # ==========================================
    # CÁLCULO 1: INDICADORES TWR E GEOMÉTRICOS
    # ==========================================
    try:
        hoje = datetime.now()
        meses_map = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 
                     7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
                     
        coluna_mes = meses_map[hoje.month]
        ano_atual = hoje.year
        label_mes = f"Rentab. {coluna_mes}/{str(ano_atual)[-2:]}"
        
        df = processar_dados_twr(arquivo_carteira).copy()
        
        # ---> RENTABILIDADE TOTAL
        rentab_total = float(df['Carteira'].iloc[-1])
        rentab_str = f"{abs(rentab_total):.2f}%"
        
        df['Fator_Cart'] = 1 + (df['Carteira'] / 100)
        
        if 'IBOV_idx' in df.columns and not df['IBOV_idx'].dropna().empty:
            ibov_ini = df['IBOV_idx'].dropna().iloc[0]
            df['Fator_IBOV'] = df['IBOV_idx'] / ibov_ini
        else:
            df['Fator_IBOV'] = 1.0
        
        # ---> AGRUPAMENTO MENSAL
        df['Ano'] = df['Data'].dt.year
        df['Mes'] = df['Data'].dt.month
        
        df_mes = df.groupby(['Ano', 'Mes']).last().reset_index()
        
        df_mes['Ret_Cart'] = df_mes['Fator_Cart'].pct_change()
        df_mes.loc[0, 'Ret_Cart'] = df_mes['Fator_Cart'].iloc[0] - 1.0
        
        df_mes['Ret_IBOV'] = df_mes['Fator_IBOV'].pct_change()
        df_mes.loc[0, 'Ret_IBOV'] = df_mes['Fator_IBOV'].iloc[0] - 1.0
        
        # Meses x IBOV
        meses_acima_str = str(int((df_mes['Ret_Cart'] > df_mes['Ret_IBOV']).sum()))
        meses_abaixo_str = str(int((df_mes['Ret_Cart'] < df_mes['Ret_IBOV']).sum()))
        
        # ---> MÉDIA DE RETORNO MENSAL (Sua Fórmula Exata)
        total_meses = len(df_mes)
        if total_meses > 0:
            # Fórmula: ((1 + Rentabilidade Total)^(1/Total de Meses))-1
            media_retorno_mensal = ((1 + (rentab_total / 100)) ** (1 / total_meses)) - 1
            media_retorno_pct = media_retorno_mensal * 100
            media_ret_str = f"{abs(media_retorno_pct):.2f}%"
        
        # Mês atual
        df_atual = df_mes[(df_mes['Ano'] == ano_atual) & (df_mes['Mes'] == hoje.month)]
        if not df_atual.empty:
            rent_mes_atual = df_atual['Ret_Cart'].iloc[0] * 100
        else:
            rent_mes_atual = df_mes['Ret_Cart'].iloc[-1] * 100
            mes_ultima_cota = meses_map[int(df_mes['Mes'].iloc[-1])]
            ano_ultima_cota = int(df_mes['Ano'].iloc[-1])
            label_mes = f"Rentab. {mes_ultima_cota}/{str(ano_ultima_cota)[-2:]}"
            
        rent_str = f"{abs(rent_mes_atual):.2f}%"

        # ---> CÁLCULOS DIÁRIOS (VaR e Volatilidade)
        df['Retorno_Diario'] = df['Fator_Cart'].pct_change()
        
        var_95 = np.percentile(df['Retorno_Diario'].dropna(), 5) * 100
        var_str = f"{var_95:.2f}%"
        
        vol_diaria = df['Retorno_Diario'].dropna().tail(252).std()
        if pd.notna(vol_diaria):
            vol_anual = vol_diaria * np.sqrt(252) * 100
            vol_str = f"{vol_anual:.2f}%"
        else:
            vol_str = "0.00%"
            
    except Exception as e:
        pass

    # ==========================================
    # CÁLCULO 2: FINANCEIRO EXATO (Capital, Ganho)
    # ==========================================
    try:
        df_patrimonio = calcular_evolucao_patrimonio(arquivo_carteira)
        capital_investido = float(df_patrimonio['Capital Investido'].dropna().iloc[-1])
        
        ganho_total = float(valor_total_carteira) - capital_investido
            
        cap_inv_str = f"R$ {capital_investido:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        ganho_str = f"R$ {abs(ganho_total):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
    except Exception as e:
        cap_inv_str = "Erro"
        ganho_str = "Erro"

    # ==========================================
    # CÁLCULO 3: SHARPE RATIO E BETA
    # ==========================================
    try:
        df_sharpe = processar_sharpe_ativos(arquivo_carteira)
        if not df_sharpe.empty and 'Carteira' in df_sharpe['Ativo'].values:
            sharpe_total = float(df_sharpe.loc[df_sharpe['Ativo'] == 'Carteira', 'Sharpe'].iloc[0])
            sharpe_str = f"{abs(sharpe_total):.2f}"
    except Exception as e:
        pass

    try:
        df_beta = processar_beta_ativos(arquivo_carteira)
        if not df_beta.empty and 'Carteira' in df_beta['Ativo'].values:
            beta_total = float(df_beta.loc[df_beta['Ativo'] == 'Carteira', 'Beta'].iloc[0])
            beta_str = f"{beta_total:.2f}"
    except Exception as e:
        pass

    # ==========================================
    # LÓGICA DE CORES E SINAIS
    # ==========================================
    def definir_cor_sinal(valor):
        if valor > 0: return "#10B981", "+" # Verde
        if valor < 0: return "#EF4444", "-" # Vermelho
        return "white", ""

    cor_mes, sinal_mes = definir_cor_sinal(rent_mes_atual)
    cor_ganho, sinal_ganho = definir_cor_sinal(ganho_total)
    cor_rentab, sinal_rentab = definir_cor_sinal(rentab_total)
    cor_sharpe, sinal_sharpe = definir_cor_sinal(sharpe_total)
    cor_media, sinal_media = definir_cor_sinal(media_retorno_pct)

    # ==========================================
    # CSS BASE E ESTILIZAÇÃO (Paleta Premium)
    # ==========================================
    st.markdown("""
        <style>
        div[data-testid="metric-container"] {
            background-color: #202020; /* Fundo Chumbo da sua paleta */
            border: 1px solid #333333;
            border-left: 4px solid #FC9149; /* Fita lateral Laranja de destaque */
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
        }
        div[data-testid="metric-container"]:hover {
            transform: translateY(-3px);
            box-shadow: 0 6px 12px rgba(252, 145, 73, 0.15); /* Brilho laranja sutil */
            border-color: #FC9149;
        }
        </style>
    """, unsafe_allow_html=True)

    def criar_card(titulo, valor, cor="white"):
        # Se a cor padrão de texto for white, vamos usar o nosso #EAEAEA para manter a harmonia
        cor_valor = "#EAEAEA" if cor == "white" else cor
        return f"""
        <div data-testid="metric-container">
            <div style="font-size: 13px; color: #EAEAEA; opacity: 0.7; padding-bottom: 0.4rem; text-transform: uppercase; letter-spacing: 0.5px;">{titulo}</div>
            <div style="font-size: 1.875rem; color: {cor_valor}; line-height: 1.2; font-weight: 700;">{valor}</div>
        </div>
        """

    # --- LINHA 1 ---
    c1, c2, c3, c4 = st.columns(4)
    with c1: 
        st.markdown(criar_card("Valor Total de Mercado", f"R$ {valor_total_carteira:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")), unsafe_allow_html=True)
    with c2: 
        st.markdown(criar_card("Rentabilidade Total", f"{sinal_rentab}{rentab_str}", cor_rentab), unsafe_allow_html=True)
    with c3: 
        st.markdown(criar_card("Volatilidade (1A)", vol_str, "white"), unsafe_allow_html=True)
    with c4: 
        st.markdown(criar_card("Beta da Carteira", beta_str, "white"), unsafe_allow_html=True)

    st.write("") 

    # --- LINHA 2 ---
    c5, c6, c7, c8 = st.columns(4)
    with c5: 
        st.markdown(criar_card("Capital Investido", cap_inv_str, "white"), unsafe_allow_html=True)
    with c6: 
        st.markdown(criar_card(label_mes, f"{sinal_mes}{rent_str}", cor_mes), unsafe_allow_html=True)
    with c7: 
        st.markdown(criar_card("VaR (95%) - 1 Dia", var_str, "white"), unsafe_allow_html=True)
    with c8: 
        st.markdown(criar_card("Meses > IBOV", meses_acima_str, "#10B981"), unsafe_allow_html=True)
    
    st.write("") 

    # --- LINHA 3 ---
    c9, c10, c11, c12 = st.columns(4)
    with c9: 
        st.markdown(criar_card("Ganho Total", f"{sinal_ganho}{ganho_str}", cor_ganho), unsafe_allow_html=True)
    with c10: 
        st.markdown(criar_card("Média Retorno Mensal", f"{sinal_media}{media_ret_str}", cor_media), unsafe_allow_html=True)
    with c11: 
        st.markdown(criar_card("Sharpe Ratio", f"{sinal_sharpe}{sharpe_str}", cor_sharpe), unsafe_allow_html=True)
    with c12: 
        st.markdown(criar_card("Meses < IBOV", meses_abaixo_str, "#EF4444"), unsafe_allow_html=True)

    st.markdown("---")