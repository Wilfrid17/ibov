import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import timedelta
import investpy

# Função para baixar e salvar ações do Ibovespa
@st.cache_data
def baixar_acoes_ibov():
    try:
        # Tentar baixar do investpy
        acoes = investpy.stocks.get_stocks(country='brazil')
        acoes_ibov = acoes[acoes['index'] == 'IBOV']
        
        # Selecionar apenas os códigos das ações
        tickers = acoes_ibov['symbol'].tolist()
        
        # Adicionar sufixo .SA para o Yahoo Finance
        tickers_sa = [ticker + ".SA" for ticker in tickers]
        
        # Criar DataFrame
        df_tickers = pd.DataFrame(tickers_sa, columns=['Código'])
        
        # Salvar arquivo CSV
        df_tickers.to_csv("IBOV.csv", sep=";", index=False)
        
        return df_tickers
    
    except Exception as e:
        st.error(f"Erro ao baixar ações do Ibovespa: {e}")
        # Fallback com lista manual de tickers importantes
        fallback_tickers = [
            "PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", 
            "B3SA3.SA", "BBAS3.SA", "ABEV3.SA", "MGLU3.SA"
        ]
        df_tickers = pd.DataFrame(fallback_tickers, columns=['Código'])
        df_tickers.to_csv("IBOV.csv", sep=";", index=False)
        return df_tickers

#cria as função de carregamento de dados
@st.cache_data
def carregar_dados(empresas):
    try:
        texto_tickers = " ".join(empresas)
        dados_acao = yf.download(texto_tickers, start="2010-01-01", end="2024-01-01")
        cotacoes_acao = dados_acao['Close']
        return cotacoes_acao
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()
    
#Carregar acoes
@st.cache_data
def carregar_tickers_acoes():
    try:
        # Verificar se o arquivo existe, se não existir, baixar
        base_tickers = pd.read_csv("IBOV.csv", sep=";")
        tickers = list(base_tickers["Código"])
        return tickers
    except FileNotFoundError:
        return baixar_acoes_ibov()["Código"].tolist()

# Baixar ações antes de iniciar o app
baixar_acoes_ibov()

# Carregar ações
acoes = carregar_tickers_acoes()
dados = carregar_dados(acoes)

st.write("""
        # App Preço de Ações 
         O gráfico abaixo representa a evolução do preço das ações ao longo dos anos
         """)

#prepara visualizações filtro
st.sidebar.header("Filtros")

# filtro de ações
lista_acoes = st.sidebar.multiselect("Escolha as ações para visualizar", dados.columns)
if lista_acoes:
    dados = dados[lista_acoes]
    if len(lista_acoes) == 1:
        acao_unica = lista_acoes[0]
        dados = dados.rename(columns={acao_unica: "Close"})
    
# Filtra de datas
data_inicial = dados.index.min().to_pydatetime()
data_final = dados.index.max().to_pydatetime()
intervalo_data = st.sidebar.slider("Selecione o período",
                                   min_value=data_inicial, 
                                   max_value=data_final,
                                   value=(data_inicial,data_final),
                                   step=timedelta(days=1))

dados = dados.loc[intervalo_data[0]:intervalo_data[1]]

#Cria o gráfico
st.line_chart(dados)

#Calcula de performance
texto_performance_ativos = "" 

if len(lista_acoes) == 0:
    lista_acoes = list(dados.columns)

#Criar carteira
carteira = [1000 for acao in lista_acoes]
total_inicial_carteira = sum(carteira)

for i, acao in enumerate(lista_acoes):
    performance_ativo = dados[acao].iloc[-1] / dados[acao].iloc[0] - 1
    performance_ativo = float(performance_ativo)
    
    carteira[i] = carteira[i] * (1 + performance_ativo)
    
    if performance_ativo > 0: 
        texto_performance_ativos =  texto_performance_ativos + f"  \n{acao}: :green[{performance_ativo:.1%}]"
    elif performance_ativo < 0:
        texto_performance_ativos =  texto_performance_ativos + f"  \n{acao}: :red[{performance_ativo:.1%}]"
    else:
        texto_performance_ativos =  texto_performance_ativos + f"  \n{acao}: {performance_ativo:.1%}"
    
total_final_carteira = sum(carteira)
performance_carteira = (total_final_carteira / total_inicial_carteira) - 1

if performance_carteira > 0: 
    texto_performance_ativos += f" performance da carteira com todos os ativos: :green[{performance_carteira:.1%}]"
elif performance_carteira < 0:
    texto_performance_ativos += f" performance da carteira com todos os ativos: :red[{performance_carteira:.1%}]"
else:
    texto_performance_ativos += f" performance da carteira com todos os ativos: {performance_carteira:.1%}"
       
st.write(f"""
        ### Performance dos Ativos 
        Essa foi a performance de ativo no período selecionado:
        
        {texto_performance_ativos}
         """)