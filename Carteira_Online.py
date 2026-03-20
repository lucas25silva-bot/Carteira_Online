import streamlit as st
import os
from processamento import processar_planilha_carteira, buscar_precos_mercado, gerar_historico_carteira
from Rentabilidade_Acumulada import plotar_grafico_historico
from Tabela_Rentabilidade_Mensal import plotar_tabela_mensal
from Valor_Mercado_Capital import plotar_grafico_patrimonio
from Risco_Retorno import plotar_grafico_risco_retorno
from Alocacao_Setorial import plotar_alocacao_setorial
from Alocacao_Tempo import plotar_alocacao_tempo
from Contribuicao_Retorno import plotar_contribuicao_retorno
from Beta_Ativos import plotar_beta_ativos
from Sharpe_Ativos import plotar_sharpe_ativos
from Correlacao_Ativos import plotar_matriz_correlacao
from tabela_multiplos import plotar_tabela_multiplos
from tabela_score import plotar_tabela_score
from tabela_target import plotar_tabela_target
from tabela_retornos import plotar_tabela_retornos
from tabela_ranking import plotar_tabela_ranking
from resumo_cards import plotar_cards_resumo
from Cotacao_Ativos import plotar_cotacao_ativos


st.set_page_config(page_title="Dashboard de Investimentos", layout="wide")

# Adiciona a paleta de cores global baseada na sua imagem
st.markdown(
    """
    <style>
    /* Fundo com degradê elegante (Do Chumbo para um tom mais escuro) */
    .stApp {
        background: linear-gradient(180deg, #202020 0%, #0A0A0A 100%) !important;
    }

    /* 1. Títulos e Subtítulos na cor Cinza Claro (#EAEAEA) */
    h1, h2, h3, h4, h5, h6 {
        color: #EAEAEA !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
        font-weight: 600 !important;
    }
    
    /* 2. Subtítulos (st.subheader) com um sublinhado charmoso Laranja (#FC9149) */
    h3 {
        border-bottom: 2px solid #FC9149;
        padding-bottom: 8px;
        margin-bottom: 1.5rem;
    }
    
    /* 3. Divisórias (st.markdown("---")) com um degradê usando o Laranja */
    hr {
        border: 0;
        height: 1px;
        background: linear-gradient(to right, transparent, #FC9149, transparent);
        margin-top: 2rem;
        margin-bottom: 2rem;
    }
    </style>
    """, 
    unsafe_allow_html=True
)

st.title("Carteira de Ações")

st.sidebar.header("Upload de Arquivos ⬇️")
upload_carteira = st.sidebar.file_uploader("1. Base Carteira Ações (Excel)", type=["xlsx", "xls"])
upload_ibov = st.sidebar.file_uploader("2. Composição IBOV (CSV)", type=["csv"])

# ==========================================
# LÓGICA DE MEMÓRIA (CACHE LOCAL)
# ==========================================
# Se o usuário fez upload agora, salvamos uma cópia na pasta
if upload_carteira is not None:
    with open("cache_carteira.xlsx", "wb") as f:
        f.write(upload_carteira.getbuffer())

if upload_ibov is not None:
    with open("cache_ibov.csv", "wb") as f:
        f.write(upload_ibov.getbuffer())

# Verifica se existe a cópia salva, mesmo que o upload esteja vazio
arquivo_carteira = "cache_carteira.xlsx" if os.path.exists("cache_carteira.xlsx") else None
arquivo_ibov = "cache_ibov.csv" if os.path.exists("cache_ibov.csv") else None
# ==========================================

if arquivo_carteira is not None and arquivo_ibov is not None:
    try:
        posicao = processar_planilha_carteira(arquivo_carteira)
        
        with st.spinner('Buscando preços em tempo real no mercado...'):
            posicao = buscar_precos_mercado(posicao)
        
        valor_total_carteira = posicao['Valor de Mercado (R$)'].sum()
        
        st.toast("Bases processadas e preços atualizados com sucesso!", icon="✅")
        

        # ALTERAÇÃO AQUI: Substitua a linha do plotar_cards_resumo antiga por esta:
        container_resumo = st.empty()

        # Insere os Cards de Resumo no topo
        plotar_cards_resumo(posicao, valor_total_carteira, arquivo_carteira)


        # ==========================================
        # FORMATAÇÃO VISUAL DA TABELA
        # ==========================================
        
        posicao_tela = posicao.rename(columns={
            'Quantidade Atual': 'Qtd Atual',
            'PM (R$)': 'Preço Médio',
            'Preço Atual (R$)': 'Preço Atual',
            'Rentabilidade (%)': 'Rentabilidade',
            'Rentabilidade com Proventos (%)': 'Rentab. c/ Prov.'
        })
        
        colunas_ordenadas = [
            'Ticker', 'Qtd Atual', 'Valor de Mercado (R$)', 
            '% na Carteira', 'Preço Médio', 'Preço Atual', 'Rentabilidade', 'Rentab. c/ Prov.'
        ]
        
        # Filtra e adiciona apenas as colunas que realmente existem na base
        colunas_presentes = [col for col in colunas_ordenadas if col in posicao_tela.columns]
        posicao_tela = posicao_tela[colunas_presentes]
        
        posicao_tela.index = range(1, len(posicao_tela) + 1)
        
        def formatar_br(valor):
            return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        def cor_rentabilidade(valor):
            if valor > 0:
                return 'color: #0a9d3b; font-weight: bold;'
            elif valor < 0:
                return 'color: #c62828; font-weight: bold;'
            return 'color: #EAEAEA;'
            
        # Dicionário de formatação inteligente
        formatacao_dict = {
            'Valor de Mercado (R$)': formatar_br,
            'Preço Médio': formatar_br,
            'Preço Atual': formatar_br,
            '% na Carteira': lambda x: f"{formatar_br(x)}%",
            'Rentabilidade': lambda x: f"{formatar_br(x)}%"
        }
        
        if 'Rentab. c/ Prov.' in posicao_tela.columns:
            formatacao_dict['Rentab. c/ Prov.'] = lambda x: f"{formatar_br(x)}%"

        posicao_estilizada = posicao_tela.style.format(formatacao_dict)
        
        try:
            colunas_cor = [c for c in ['Rentabilidade', 'Rentab. c/ Prov.'] if c in posicao_tela.columns]
            posicao_estilizada = posicao_estilizada.map(cor_rentabilidade, subset=colunas_cor)
        except AttributeError:
            posicao_estilizada = posicao_estilizada.applymap(cor_rentabilidade, subset=colunas_cor)

        st.subheader("Posição Atual")
        st.dataframe(posicao_estilizada, use_container_width=True)
        
        # ==========================================
        # GRÁFICO HISTÓRICO COM FILTRO DE DATA
        # ==========================================
        
        
        # O gráfico gera a imagem e devolve o valor matemático correto
        rentabilidade_correta = plotar_grafico_historico(arquivo_carteira)

        # Para:
        df_rent_mensal = plotar_tabela_mensal(arquivo_carteira)
        
        # Insere o gráfico de Evolução do Patrimônio
        plotar_grafico_patrimonio(arquivo_carteira)
        
        # Insere o gráfico de Risco x Retorno
        plotar_grafico_risco_retorno(arquivo_carteira)
        
        # Insere os gráficos de Alocação Setorial e de Ativos
        plotar_alocacao_setorial(arquivo_carteira)
        
        # Insere o gráfico de Alocação ao Longo do Tempo
        plotar_alocacao_tempo(arquivo_carteira)
        
        # Divide a tela para colocar Beta e Sharpe lado a lado
        col_beta, col_sharpe = st.columns(2)
        
        with col_beta:
            plotar_beta_ativos(arquivo_carteira)
            
        with col_sharpe:
            plotar_sharpe_ativos(arquivo_carteira)
        
        # Insere a Matriz de Correlação
        plotar_matriz_correlacao(arquivo_carteira)
        
        # Insere a Tabela de Score Fundamentalista
        plotar_tabela_score(posicao, arquivo_ibov)

        # Insere a Tabela de Target Price
        plotar_tabela_target(posicao, arquivo_ibov)

        # Insere a Tabela de Retornos Históricos (NOVO)
        plotar_tabela_retornos(posicao, arquivo_ibov)

        # Insere o Ranking Geral Unificado
        st.markdown("---") # Coloca uma linha divisória charmosa para separar o Ranking
        plotar_tabela_ranking(posicao, arquivo_ibov)

        # Insere o módulo de Cotação dos Ativos e Preço Médio
        plotar_cotacao_ativos(arquivo_carteira, arquivo_ibov)

    except Exception as e:
        st.error(f"Erro ao processar as bases. Verifique os arquivos. Detalhe: {e}")

else:
    st.info("👈 Por favor, faça o upload dos dois arquivos na barra lateral para gerar o dashboard.")