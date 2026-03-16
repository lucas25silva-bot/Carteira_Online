import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px

@st.cache_data(show_spinner=False, ttl=3600)
def processar_alocacao(arquivo_carteira):
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
    df_neg['Quantidade'] = pd.to_numeric(df_neg['Quantidade'], errors='coerce').fillna(0)
    
    df_neg['Qtd_Sinal'] = np.where(
        df_neg['Tipo de Movimentação'].str.upper().str.contains('COMPRA'),
        df_neg['Quantidade'], -df_neg['Quantidade']
    )
    
    posicao = df_neg.groupby('Ticker')['Qtd_Sinal'].sum()
    ativos_ativos = posicao[posicao > 0].index.tolist()
    
    if not ativos_ativos:
        return pd.DataFrame()
        
    mapa_setores_pt = {
        'Financial Services': 'Financeiro', 'Healthcare': 'Saúde', 'Technology': 'Tecnologia',
        'Industrials': 'Bens Industriais', 'Consumer Cyclical': 'Consumo Cíclico',
        'Consumer Defensive': 'Consumo Não Cíclico', 'Basic Materials': 'Materiais Básicos / Siderurgia',
        'Energy': 'Petróleo e Gás', 'Utilities': 'Energia Elétrica', 'Real Estate': 'Imobiliário',
        'Communication Services': 'Comunicações'
    }

    # Dicionário de Setores da B3
    mapa_b3_setor = {
        'ITSA4': 'Financeiro', 'ITSA3': 'Financeiro', 'ITUB4': 'Financeiro', 'ITUB3': 'Financeiro',
        'BBDC4': 'Financeiro', 'BBDC3': 'Financeiro', 'BBAS3': 'Financeiro', 'B3SA3': 'Financeiro',
        'BPAC11': 'Financeiro', 'SANB11': 'Financeiro', 'BBSE3': 'Financeiro', 'CXSE3': 'Financeiro',
        'PSSA3': 'Financeiro', 'IRBR3': 'Financeiro', 'BRSR6': 'Financeiro', 'ABCB4': 'Financeiro',
        'ELET3': 'Energia Elétrica', 'ELET6': 'Energia Elétrica', 'EQTL3': 'Energia Elétrica',
        'CPLE6': 'Energia Elétrica', 'CMIG4': 'Energia Elétrica', 'ENGI11': 'Energia Elétrica',
        'TAEE11': 'Energia Elétrica', 'TRPL4': 'Energia Elétrica', 'ISAE4': 'Energia Elétrica',
        'ALUP11': 'Energia Elétrica', 'EGIE3': 'Energia Elétrica', 'NEOE3': 'Energia Elétrica',
        'AURE3': 'Energia Elétrica', 'SBSP3': 'Saneamento', 'CSMG3': 'Saneamento', 'SAPR11': 'Saneamento',
        'SAPR4': 'Saneamento', 'PETR4': 'Petróleo e Gás', 'PETR3': 'Petróleo e Gás', 'PRIO3': 'Petróleo e Gás',
        'BRAV3': 'Petróleo e Gás', 'RECV3': 'Petróleo e Gás', 'ENAT3': 'Petróleo e Gás',
        'CSAN3': 'Petróleo e Gás', 'UGPA3': 'Petróleo e Gás', 'VBBR3': 'Petróleo e Gás',
        'VALE3': 'Materiais Básicos / Siderurgia', 'SUZB3': 'Materiais Básicos / Siderurgia',
        'KLBN11': 'Materiais Básicos / Siderurgia', 'CSNA3': 'Materiais Básicos / Siderurgia',
        'GGBR4': 'Materiais Básicos / Siderurgia', 'GOAU4': 'Materiais Básicos / Siderurgia',
        'USIM5': 'Materiais Básicos / Siderurgia', 'BRAP4': 'Materiais Básicos / Siderurgia',
        'CMIN3': 'Materiais Básicos / Siderurgia', 'CBAV3': 'Materiais Básicos / Siderurgia',
        'DXCO3': 'Materiais Básicos / Siderurgia', 'WEGE3': 'Bens Industriais', 'EMBR3': 'Bens Industriais',
        'CCRO3': 'Bens Industriais', 'RAIL3': 'Bens Industriais', 'AZUL4': 'Bens Industriais',
        'GOLL4': 'Bens Industriais', 'STBP3': 'Bens Industriais', 'POMO4': 'Bens Industriais',
        'TUPY3': 'Bens Industriais', 'LREN3': 'Consumo Cíclico', 'MGLU3': 'Consumo Cíclico',
        'ARZZ3': 'Consumo Cíclico', 'ALOS3': 'Consumo Cíclico', 'PETZ3': 'Consumo Cíclico',
        'SOMA3': 'Consumo Cíclico', 'CEAB3': 'Consumo Cíclico', 'GUAR3': 'Consumo Cíclico',
        'CVCB3': 'Consumo Cíclico', 'COGN3': 'Consumo Cíclico', 'YDUQ3': 'Consumo Cíclico',
        'RENT3': 'Consumo Cíclico', 'MOVI3': 'Consumo Cíclico', 'VAMO3': 'Consumo Cíclico',
        'SMFT3': 'Consumo Cíclico', 'VIVA3': 'Consumo Cíclico', 'ABEV3': 'Consumo Não Cíclico',
        'JBSS3': 'Consumo Não Cíclico', 'BRFS3': 'Consumo Não Cíclico', 'CRFB3': 'Consumo Não Cíclico',
        'ASAI3': 'Consumo Não Cíclico', 'SMTO3': 'Consumo Não Cíclico', 'SLCE3': 'Consumo Não Cíclico',
        'MRFG3': 'Consumo Não Cíclico', 'BEEF3': 'Consumo Não Cíclico', 'PCAR3': 'Consumo Não Cíclico',
        'CAML3': 'Consumo Não Cíclico', 'RADL3': 'Saúde', 'RDOR3': 'Saúde', 'HAPV3': 'Saúde',
        'FLRY3': 'Saúde', 'MATD3': 'Saúde', 'QUAL3': 'Saúde', 'BLAU3': 'Saúde', 'VVEO3': 'Saúde',
        'PNVL3': 'Saúde', 'TOTS3': 'Tecnologia', 'LWSA3': 'Tecnologia', 'VIVT3': 'Comunicações',
        'TIMS3': 'Comunicações', 'MULT3': 'Imobiliário', 'IGTI11': 'Imobiliário', 'CYRE3': 'Imobiliário',
        'EZTC3': 'Imobiliário', 'MRVE3': 'Imobiliário', 'DIRR3': 'Imobiliário', 'JHSF3': 'Imobiliário',
        'HBOR3': 'Imobiliário'
    }

    # Novo Dicionário de Segmentos da B3
    mapa_b3_segmento = {
        'ITSA4': 'Bancos', 'ITSA3': 'Bancos', 'ITUB4': 'Bancos', 'ITUB3': 'Bancos',
        'BBDC4': 'Bancos', 'BBDC3': 'Bancos', 'BBAS3': 'Bancos', 'ABCB4': 'Bancos', 'BRSR6': 'Bancos', 'SANB11': 'Bancos', 'BPAC11': 'Bancos',
        'B3SA3': 'Serviços Financeiros Diversos',
        'BBSE3': 'Seguradoras', 'CXSE3': 'Seguradoras', 'PSSA3': 'Seguradoras', 'IRBR3': 'Resseguradoras',
        'ELET3': 'Geração de Energia', 'ELET6': 'Geração de Energia', 'EQTL3': 'Distribuição de Energia',
        'CPLE6': 'Energia Integrada', 'CMIG4': 'Energia Integrada', 'ENGI11': 'Distribuição de Energia',
        'TAEE11': 'Transmissão de Energia', 'TRPL4': 'Transmissão de Energia', 'ISAE4': 'Transmissão de Energia',
        'ALUP11': 'Transmissão de Energia', 'EGIE3': 'Geração de Energia', 'NEOE3': 'Energia Integrada', 'AURE3': 'Geração de Energia',
        'SBSP3': 'Água e Saneamento', 'CSMG3': 'Água e Saneamento', 'SAPR11': 'Água e Saneamento', 'SAPR4': 'Água e Saneamento',
        'PETR4': 'Exploração e Refino', 'PETR3': 'Exploração e Refino', 'PRIO3': 'Exploração e Refino',
        'BRAV3': 'Exploração e Refino', 'RECV3': 'Exploração e Refino', 'ENAT3': 'Exploração e Refino',
        'CSAN3': 'Distribuição de Combustíveis', 'UGPA3': 'Distribuição de Combustíveis', 'VBBR3': 'Distribuição de Combustíveis',
        'VALE3': 'Minerais Metálicos', 'BRAP4': 'Minerais Metálicos', 'CMIN3': 'Minerais Metálicos', 'CBAV3': 'Alumínio',
        'SUZB3': 'Papel e Celulose', 'KLBN11': 'Papel e Celulose',
        'CSNA3': 'Siderurgia', 'GGBR4': 'Siderurgia', 'GOAU4': 'Siderurgia', 'USIM5': 'Siderurgia',
        'DXCO3': 'Madeira e Construção',
        'WEGE3': 'Máquinas e Equipamentos', 'EMBR3': 'Material Aeronáutico',
        'CCRO3': 'Exploração de Rodovias', 'RAIL3': 'Transporte Ferroviário', 'STBP3': 'Serviços Portuários',
        'AZUL4': 'Transporte Aéreo', 'GOLL4': 'Transporte Aéreo',
        'LREN3': 'Fios e Tecidos / Vestuário', 'SOMA3': 'Fios e Tecidos / Vestuário', 'ARZZ3': 'Calçados', 'CEAB3': 'Fios e Tecidos / Vestuário', 'GUAR3': 'Fios e Tecidos / Vestuário',
        'MGLU3': 'Eletrodomésticos', 'PETZ3': 'Comércio Especializado',
        'ALOS3': 'Exploração de Imóveis', 'MULT3': 'Exploração de Imóveis', 'IGTI11': 'Exploração de Imóveis',
        'CVCB3': 'Viagens e Turismo', 'COGN3': 'Serviços Educacionais', 'YDUQ3': 'Serviços Educacionais',
        'RENT3': 'Aluguel de Carros', 'MOVI3': 'Aluguel de Carros', 'VAMO3': 'Aluguel de Máquinas',
        'SMFT3': 'Serviços Diversos', 'VIVA3': 'Cosméticos',
        'ABEV3': 'Cervejas e Refrigerantes',
        'JBSS3': 'Carnes e Derivados', 'BRFS3': 'Carnes e Derivados', 'MRFG3': 'Carnes e Derivados', 'BEEF3': 'Carnes e Derivados',
        'CRFB3': 'Alimentos / Supermercados', 'ASAI3': 'Alimentos / Supermercados', 'PCAR3': 'Alimentos / Supermercados',
        'CAML3': 'Alimentos Diversos', 'SMTO3': 'Açúcar e Álcool', 'SLCE3': 'Agricultura',
        'RADL3': 'Medicamentos', 'PNVL3': 'Medicamentos',
        'RDOR3': 'Serviços Médico-Hospitalares', 'HAPV3': 'Serviços Médico-Hospitalares', 'FLRY3': 'Serviços Médico-Hospitalares', 'MATD3': 'Serviços Médico-Hospitalares',
        'TOTS3': 'Programas e Serviços', 'LWSA3': 'Programas e Serviços',
        'VIVT3': 'Telecomunicações', 'TIMS3': 'Telecomunicações',
        'CYRE3': 'Edificações', 'EZTC3': 'Edificações', 'MRVE3': 'Edificações', 'DIRR3': 'Edificações', 'JHSF3': 'Edificações', 'HBOR3': 'Edificações'
    }

    dados_alocacao = []
    tickers_yf = [f"{t}.SA" for t in ativos_ativos]
    
    try:
        dados_raw = yf.download(tickers_yf, period="5d", progress=False)
        if isinstance(dados_raw.columns, pd.MultiIndex):
            dados_mkt = dados_raw['Close'] if 'Close' in dados_raw.columns.get_level_values(0) else dados_raw
        elif 'Close' in dados_raw.columns:
            dados_mkt = dados_raw[['Close']].rename(columns={'Close': tickers_yf[0]}) if len(tickers_yf) == 1 else dados_raw
        else:
            dados_mkt = dados_raw
    except:
        dados_mkt = pd.DataFrame()

    for t in ativos_ativos:
        qtd = posicao[t]
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
                preco_atual = 1.0 
                
        valor_mercado = qtd * preco_atual
        setor = "Outros"
        segmento = "Outros"
        
        # LÓGICA DE CLASSIFICAÇÃO: SETOR E SEGMENTO
        if t in mapa_b3_setor:
            setor = mapa_b3_setor[t]
            segmento = mapa_b3_segmento.get(t, "Outros")
        elif t[-2:] in ['33', '34', '35', '39']:
            setor = "Exterior (BDR)"
            segmento = "Ações Internacionais"
        elif t in ['BOVA11', 'IVVB11', 'SMAL11', 'HASH11', 'NASD11', 'DIVO11', 'FIXA11', 'BINA11', 'XINA11', 'GOLD11']:
            setor = "ETFs"
            segmento = "Fundos de Índice"
        elif t.endswith('11') and t not in ['BPAC11', 'SANB11', 'TAEE11', 'ALUP11', 'ENGI11', 'SAPR11', 'KLBN11', 'IGTI11']:
            setor = "Fundos Imobiliários (FII)"
            segmento = "Fundos Imobiliários (FII)"
        else:
            try:
                info = yf.Ticker(ticker_sa).info
                if info.get('quoteType') == 'ETF':
                    setor = "ETFs"
                    segmento = "Fundos de Índice"
                else:
                    setor_eng = info.get('sector')
                    seg_eng = info.get('industry')
                    if setor_eng: setor = mapa_setores_pt.get(setor_eng, setor_eng)
                    if seg_eng: segmento = seg_eng # Mantém em inglês se for empresa fora do radar
            except:
                pass
                
        dados_alocacao.append({
            'Ativo': t,
            'Setor': setor,
            'Segmento': segmento,
            'Valor de Mercado': valor_mercado
        })
        
    df_alocacao = pd.DataFrame(dados_alocacao)
    total_patrimonio = df_alocacao['Valor de Mercado'].sum()
    if total_patrimonio > 0:
        df_alocacao['% Carteira'] = (df_alocacao['Valor de Mercado'] / total_patrimonio) * 100
    else:
        df_alocacao['% Carteira'] = 0.0
    
    return df_alocacao

def plotar_alocacao_setorial(arquivo_carteira):
    st.markdown("---")
    st.subheader("Diversificação e Alocação da Carteira")
    
    with st.spinner("Classificando os setores e segmentos da carteira..."):
        df_aloc = processar_alocacao(arquivo_carteira)
        
    if not df_aloc.empty:
        # ========================================================
        # NOVO: DICIONÁRIO UNIVERSAL DE CORES DA CARTEIRA
        # ========================================================
        MAPA_CORES_SETORES = {
            'Financeiro': '#3A86FF',
            'Energia Elétrica': '#FFBE0B',
            'Petróleo e Gás': '#FB5607',
            'Materiais Básicos / Siderurgia': '#8338EC',
            'Bens Industriais': '#8D6E63',
            'Consumo Cíclico': "#C0131B",
            'Consumo Não Cíclico': '#2ECC71',
            'Saúde': '#06D6A0',
            'Tecnologia': '#00BBF9',
            'Comunicações': '#F15BB5',
            'Imobiliário': '#F8961E',
            'Saneamento': '#4CC9F0',
            'Fundos Imobiliários (FII)': '#7209B7',
            'Exterior (BDR)': '#90DBF4',
            'ETFs': '#43AA8B',
            'Outros': '#ADB5BD'
        }
        
        # GRÁFICO ÚNICO: FUNIL POR SETOR
        df_setor = df_aloc.groupby('Setor', as_index=False).agg({'Valor de Mercado': 'sum', '% Carteira': 'sum'})
        df_setor = df_setor.sort_values(by='Valor de Mercado', ascending=True)
        
        fig_setor = px.funnel(
            df_setor, 
            y='Setor', 
            x='Valor de Mercado',
            color='Setor',
            text='% Carteira', 
            color_discrete_map=MAPA_CORES_SETORES # <-- Aplica a cor fixa aqui!
        )
        fig_setor.update_traces(
            texttemplate="%{text:.2f}%",
            textposition="inside",
            hovertemplate="<b>%{y}</b><br>Patrimônio: R$ %{x:,.2f}<br>Peso: %{text:.2f}%<extra></extra>"
        )
        fig_setor.update_layout(
            title="<b>Por Setor</b>",
            title_x=0.5,
            showlegend=False,
            margin=dict(t=50, b=20, l=20, r=20),
            height=450,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis_title="",
            xaxis_title=""
        )
        
        st.plotly_chart(fig_setor, use_container_width=True)
            
        # TABELA DE DETALHES (MANTENDO O SEGMENTO)
        with st.expander("📊 Ver Tabela de Alocação Detalhada", expanded=False):
            df_tabela = df_aloc.sort_values(by='% Carteira', ascending=False).copy()
            
            def formatar_br(valor):
                if pd.isna(valor): return "R$ 0,00"
                return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                
            df_tabela['Valor de Mercado'] = df_tabela['Valor de Mercado'].apply(formatar_br)
            df_tabela['% Carteira'] = df_tabela['% Carteira'].apply(lambda x: f"{x:.2f}%")
            
            df_tabela = df_tabela[['Ativo', 'Setor', 'Segmento', 'Valor de Mercado', '% Carteira']]
            
            st.dataframe(df_tabela.set_index('Ativo'), use_container_width=True)
            
    else:
        st.warning("Não há ativos suficientes na carteira para gerar os gráficos de alocação.")