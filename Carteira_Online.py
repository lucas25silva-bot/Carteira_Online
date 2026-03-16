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



st.set_page_config(page_title="Dashboard de Investimentos", layout="wide")

# Adiciona o fundo em degradê
st.markdown(
    """
    <style>
    .stApp {
        /* Altere o ângulo e as cores abaixo para testar */
        background: linear-gradient(135deg, #001937 0%, #000000 100%);
        background-attachment: fixed;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Acompanhamento da Carteira")

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
        
        st.subheader("Resumo da Carteira")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                label="Valor Total de Mercado", 
                value=f"R$ {valor_total_carteira:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )

        # Cria uma "caixa vazia" na coluna 2 para receber o valor do gráfico depois
        caixa_rentabilidade = col2.empty()
        
        # ==========================================
        # FORMATAÇÃO VISUAL DA TABELA
        # ==========================================
        
        posicao_tela = posicao.rename(columns={
            'Quantidade Atual': 'Qtd Atual',
            'PM (R$)': 'Preço Médio',
            'Preço Atual (R$)': 'Preço Atual',
            'Rentabilidade (%)': 'Rentabilidade'
        })
        
        colunas_ordenadas = [
            'Ticker', 'Qtd Atual', 'Valor de Mercado (R$)', 
            '% na Carteira', 'Preço Médio', 'Preço Atual', 'Rentabilidade'
        ]
        posicao_tela = posicao_tela[colunas_ordenadas]
        
        posicao_tela.index = range(1, len(posicao_tela) + 1)
        
        def formatar_br(valor):
            return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        def cor_rentabilidade(valor):
            if valor > 0:
                return 'color: #0a9d3b; font-weight: bold;'
            elif valor < 0:
                return 'color: #c62828; font-weight: bold;'
            return 'color: black;'
            
        posicao_estilizada = posicao_tela.style.format({
            'Valor de Mercado (R$)': formatar_br,
            'Preço Médio': formatar_br,
            'Preço Atual': formatar_br,
            '% na Carteira': lambda x: f"{formatar_br(x)}%",
            'Rentabilidade': lambda x: f"{formatar_br(x)}%"
        })
        
        try:
            posicao_estilizada = posicao_estilizada.map(cor_rentabilidade, subset=['Rentabilidade'])
        except AttributeError:
            posicao_estilizada = posicao_estilizada.applymap(cor_rentabilidade, subset=['Rentabilidade'])

        st.subheader("Sua Posição Atual")
        st.dataframe(posicao_estilizada, use_container_width=True)
        
        # ==========================================
        # GRÁFICO HISTÓRICO COM FILTRO DE DATA
        # ==========================================
        
        # O gráfico gera a imagem e devolve o valor matemático correto
        rentabilidade_correta = plotar_grafico_historico(arquivo_carteira)
        
        # Insere a Tabela de Rentabilidade Mensal logo abaixo do gráfico
        plotar_tabela_mensal(arquivo_carteira)
        
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

        # Insere a Tabela de Múltiplos
        plotar_tabela_multiplos(posicao, arquivo_ibov)

        # Preenche aquela "caixa vazia" lá no topo com o valor exato
        caixa_rentabilidade.metric(
            label="Rentabilidade da Carteira", 
            value=f"{rentabilidade_correta:.2f}%"
        )

    except Exception as e:
        st.error(f"Erro ao processar as bases. Verifique os arquivos. Detalhe: {e}")

else:
    st.info("👈 Por favor, faça o upload dos dois arquivos na barra lateral para gerar o dashboard.")