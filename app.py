import streamlit as st
import pandas as pd
from google.oauth2.service_account import Credentials
import gspread
from streamlit_option_menu import option_menu
import plotly.graph_objects as go
from sheet_helper import get_googlesheet_client, load_sheet, download_sheet
from sheet_ids import CREDENTIALS_SPREADSHEET_ID, DATABASE_ID

# Função para autenticar o usuário
def autenticar_usuario(login, senha, users_data):
    for user in users_data:
        if user['login'] == login and str(user['senha']) == senha:
            if user['status'] == 'Ativo':
                return user
            else:
                return None  # Se o status for 'Inativo', não permite o login
    return None
#teste
# Função principal
def main():
    # Verificar se o usuário está logado (usando session_state)
    if 'usuario_logado' not in st.session_state:
        # Definir layout como "centered" para a tela de login
        st.set_page_config(
        page_title="Amicis Control",  # Título exibido na aba do navegador
        #page_icon="📊",       # Ícone exibido na aba do navegador
        page_icon=r"images/favicon.png",  # Caminho para o favicon
        layout="centered",        # Layout da página: "centered" ou "wide"
        initial_sidebar_state="expanded"  # Estado inicial da barra lateral: "expanded", "collapsed", ou "auto"
    )

        st.image(r"images/logo.png", width=300)

        #DIEGUERA
        # Tela de Login
        st.title("Amicis Control")
        
        login = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        
        if st.button("Entrar"):
            client = get_googlesheet_client()
            
            # Carregar dados da planilha
            users_data = load_sheet(CREDENTIALS_SPREADSHEET_ID).sheet1.get_all_records()
    
            # Verificar login e senha
            usuario = autenticar_usuario(login, senha, users_data)
            
            if usuario:
                st.session_state.usuario_logado = usuario  # Armazenar o usuário logado
                st.session_state.is_logged_in = True  # Flag indicando que o usuário está logado
                st.success(f"Bem-vindo, {usuario['nome']}!")
                st.rerun()  # Força o re-carregamento da página
            else:
                st.error("Login ou senha incorretos, ou o seu cadastro está inativo.")
    else:
        # Definir layout como "wide" para as outras páginas após o login
        st.set_page_config(layout="wide")

        # Exibir conteúdo após o login
        st.title("Amicis Control - Controle de Operações")

        # Carregar os dados do arquivo Excel
         # Carregar os dados do arquivo Excel
        # file_path = r"data/database.xlsx"
        # df = pd.read_excel(file_path, sheet_name="Base")
        df = download_sheet(DATABASE_ID)

        # Verificar se há uma coluna 'Ano'; caso contrário, criar com base na data
        if 'Ano' not in df.columns:
            df['Ano'] = pd.to_datetime(df['Data']).dt.year  # Supondo que a coluna de data seja 'Data'

        # Certificar-se de que a coluna de data está no formato datetime
        df['Data'] = pd.to_datetime(df['Data'])

        # Criando o menu lateral
        with st.sidebar:
            st.image(r"images\logo.png", width=300)
            selected = option_menu(
                "Menu",
                ["Dashboard", "Resultado Mês", "Resultado por Ativo", "Resultado por Estratégia"],
                icons=["house", "bar-chart", "currency-exchange", "clipboard-data"],
                menu_icon="cast",
                default_index=0,
            )

        # Filtros no topo da página
        filtros_container = st.container()
        with filtros_container:
            #st.subheader("Filtros Globais")
            col1, col2, col3, col4, col5 = st.columns(5)
            
            # Inicializar DataFrame filtrado
            df_filtrado = df.copy()
            
            with col1:
                # Filtro de Ano
                anos_disponiveis = ['Todos'] + sorted(df_filtrado['Ano'].unique())
                ano = st.selectbox("Escolha o Ano", anos_disponiveis)
                if ano != 'Todos':
                    df_filtrado = df_filtrado[df_filtrado["Ano"] == int(ano)]

            with col2:
                # Filtro de Mês
                meses_disponiveis = ['Todos'] + sorted(df_filtrado['Mês'].unique())
                mes = st.selectbox("Escolha o Mês", meses_disponiveis)
                if mes != 'Todos':
                    df_filtrado = df_filtrado[df_filtrado["Mês"] == mes]

            with col3:
                # Filtro de Ativo
                ativos_disponiveis = ['Todos'] + sorted(df_filtrado['Ativo'].unique())
                ativo = st.selectbox("Escolha o Ativo", ativos_disponiveis)
                if ativo != 'Todos':
                    df_filtrado = df_filtrado[df_filtrado["Ativo"] == ativo]

            with col4:
                # Filtro de Setup
                setups_disponiveis = ['Todos'] + sorted(df_filtrado["Setup"].unique())
                setup_selecionado = st.selectbox("Escolha o Setup", setups_disponiveis)
                if setup_selecionado != 'Todos':
                    df_filtrado = df_filtrado[df_filtrado["Setup"] == setup_selecionado]

            with col5:
                # Filtro de Intervalo de Datas
                start_date, end_date = st.date_input(
                    "Escolha o Intervalo de Datas",
                    value=(df_filtrado['Data'].min(), df_filtrado['Data'].max()),
                    min_value=df_filtrado['Data'].min(),
                    max_value=df_filtrado['Data'].max(),
                    format="DD/MM/YYYY"
                )
                df_filtrado = df_filtrado[(df_filtrado['Data'] >= pd.Timestamp(start_date)) & 
                                          (df_filtrado['Data'] <= pd.Timestamp(end_date))]

                # Adicionar opção para limpar o filtro
                if st.button('Limpar Intervalo'):
                    ano = 'Todos'
                    mes = 'Todos'
                    ativo = 'Todos'
                    setup_selecionado = 'Todos'
                    start_date, end_date = df['Data'].min(), df['Data'].max()
                    df_filtrado = df.copy()


        # Filtrar os dados com base nas escolhas
        df_filtrado = df.copy()

        # Filtro por Ano
        if ano != 'Todos':
            df_filtrado = df_filtrado[df_filtrado["Ano"] == int(ano)]

        # Filtro por Mês
        if mes != 'Todos':
            df_filtrado = df_filtrado[df_filtrado["Mês"] == mes]

        # Filtro por Ativo
        if ativo != 'Todos':
            df_filtrado = df_filtrado[df_filtrado["Ativo"] == ativo]

        # Filtro por Setup
        if setup_selecionado != 'Todos':
            df_filtrado = df_filtrado[df_filtrado["Setup"] == setup_selecionado]

        # Filtro por Intervalo de Datas
        df_filtrado = df_filtrado[(df_filtrado['Data'] >= pd.Timestamp(start_date)) & 
                                (df_filtrado['Data'] <= pd.Timestamp(end_date))]



            #
        # Função para estilizar as métricas com cores dinâmicas


        def format_metric(label, value, bg_color="rgb(51, 51, 51)", font_color="rgb(255, 255, 255)", 
                        positive_color="rgb(33, 145, 33)", negative_color="rgb(255, 0, 0)", 
                        neutral_color="rgb(255, 255, 255)", orange_color="rgb(210, 143, 90)", 
                        blue_color="rgb(85, 126, 188)"):
            value = float(value)  # Garantir que o valor seja numérico (float)
            
            # Formatando valores conforme solicitado
            if label == "Lucro/Prejuízo (R$)":
                formatted_value = f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            elif label in ["Taxa de Acerto (%)", "Breakeven (%)", "Edge (%)"]:
                formatted_value = f"{value:.2f}%".replace(".", ",")
            elif label in ["Risco/Retorno", "Fator de Lucro"]:
                formatted_value = f"{value:.2f}".replace(".", ",")
            else:
                formatted_value = f"{value:.2f}"  # Formato genérico caso não se encaixe nas categorias
            
            # Definindo a cor dinâmica para cada tipo de métrica
            if label == "Lucro/Prejuízo (R$)":
                if value > 0:
                    color = positive_color  # Verde para lucro
                elif value < 0:
                    color = negative_color  # Vermelho para prejuízo
                else:
                    color = neutral_color  # Branco para zero
            elif label == "Fator de Lucro":
                if value > 1:
                    color = positive_color  # Verde para fator de lucro > 1
                elif value < 1:
                    color = negative_color  # Vermelho para fator de lucro < 1
                else:
                    color = neutral_color  # Branco para fator de lucro igual a 1
            elif label == "Edge (%)":
                if value > 0:
                    color = positive_color  # Verde para Edge positivo
                elif value < 0:
                    color = negative_color  # Vermelho para Edge negativo
                else:
                    color = neutral_color  # Branco para Edge igual a 0
            elif label == "Risco/Retorno":
                color = orange_color  # Laranja para risco/retorno
            elif label == "Breakeven (%)":
                color = blue_color  # Azul para breakeven
            elif label == "Taxa de Acerto (%)":
                color = neutral_color  # Branco para taxa de acerto
            
            # Retorna o HTML formatado
            return f"""
                <div style="
                    background-color: {bg_color};
                    border-radius: 8px;
                    padding: 10px;
                    margin: 5px;
                    text-align: center;">
                    <p style="margin: 0; font-size: 16px; font-weight: bold; color: {font_color};">{label}</p>
                    <p style="margin: 0; font-size: 24px; font-weight: bold; color: {color};">{formatted_value}</p>
                </div>
            """
        


        # Mostra a página selecionada
        if selected == "Dashboard":
            st.header("Dashboard")
            # Adicionar código do Dashboard aqui


             # Calculando as métricas
            lucro_prejuizo = df_filtrado["R$"].sum()
            num_gain = len(df_filtrado[df_filtrado["Gain/Loss"] == "Gain"])
            num_loss = len(df_filtrado[df_filtrado["Gain/Loss"] == "Loss"])
            num_draw = len(df_filtrado[df_filtrado["Gain/Loss"] == "Draw"])
            total_trades = num_gain + num_loss + num_draw
            taxa_acerto = num_gain / (num_gain + num_loss) * \
                100 if total_trades > 0 else 0
            avg_gain = df_filtrado[df_filtrado["Gain/Loss"] == "Gain"]["R$"].mean()
            avg_loss = df_filtrado[df_filtrado["Gain/Loss"] == "Loss"]["R$"].mean()
            risco_retorno = avg_gain / abs(avg_loss) if avg_loss != 0 else 0
            breakeven = (1 / (1 + risco_retorno) * 100) if risco_retorno > 0 else 0
            edge = taxa_acerto - breakeven if breakeven > 0 else 0
            total_gain = df_filtrado[df_filtrado["Gain/Loss"] == "Gain"]["R$"].sum()
            total_loss = df_filtrado[df_filtrado["Gain/Loss"] == "Loss"]["R$"].sum()
            fator_lucro = total_gain / abs(total_loss) if total_loss != 0 else 0

            # Calculando o melhor trade (Gain) e a maior perda (Loss)
            best_trade = df_filtrado[df_filtrado["Gain/Loss"] == "Gain"]["R$"].max(
            ) if not df_filtrado[df_filtrado["Gain/Loss"] == "Gain"].empty else 0
            worst_trade = df_filtrado[df_filtrado["Gain/Loss"] == "Loss"]["R$"].min(
            ) if not df_filtrado[df_filtrado["Gain/Loss"] == "Loss"].empty else 0

            # Dividindo em 6 colunas lado a lado
            col1, col2, col3, col4, col5, col6 = st.columns(6)

            with col1:
                st.markdown(format_metric("Lucro/Prejuízo (R$)",
                            lucro_prejuizo), unsafe_allow_html=True)
            with col2:
                st.markdown(format_metric("Taxa de Acerto (%)",
                            taxa_acerto), unsafe_allow_html=True)
            with col3:
                st.markdown(format_metric("Risco/Retorno", risco_retorno),
                            unsafe_allow_html=True)
            with col4:
                st.markdown(format_metric("Breakeven (%)", breakeven),
                            unsafe_allow_html=True)
            with col5:
                st.markdown(format_metric("Edge (%)", edge), unsafe_allow_html=True)
            with col6:
                st.markdown(format_metric("Fator de Lucro", fator_lucro),
                            unsafe_allow_html=True)

            
            
            # Criando colunas para os gráficos lado a lado
            col1, col2, col3, col4 = st.columns([1, 1, 1, 2])

            # Gráfico de Nº de Trades
            with col1:
                st.markdown("<h3 style='font-weight:bold;'>Número de Trades</h3>", unsafe_allow_html=True)

                # Calculando o número de Gain, Loss, Draw e Total de Trades
                num_gain = len(df_filtrado[df_filtrado["Gain/Loss"] == "Gain"])
                num_loss = len(df_filtrado[df_filtrado["Gain/Loss"] == "Loss"])
                num_draw = len(df_filtrado[df_filtrado["Gain/Loss"] == "Draw"])
                total_trades = num_gain + num_loss + num_draw

                # Criando um DataFrame com os dados para o gráfico de barras
                trade_data = {
                    "Tipo": ["Gain", "Loss", "Draw", "Total"],
                    "Número de Trades": [num_gain, num_loss, num_draw, total_trades],
                    "Cor": ["green", "red", "blue", "gray"],
                }

                trade_df_filtrado = pd.DataFrame(trade_data)

                # Função para definir o texto dentro ou fora das barras
                def get_textposition(value):
                    return "inside" if value > 50 else "outside"

                # Gráfico de Barras
                fig_trades = go.Figure(go.Bar(
                    x=trade_df_filtrado["Tipo"],
                    y=trade_df_filtrado["Número de Trades"],
                    marker=dict(color=trade_df_filtrado["Cor"]),
                    text=[f"{v}" for v in trade_df_filtrado["Número de Trades"]],
                    textposition=[get_textposition(v) for v in trade_df_filtrado["Número de Trades"]],
                    textfont=dict(color='white', size=14, family="Arial, sans-serif", weight="bold"),  # Negrito nos dados
                    width=0.7
                ))

                # Ajustando o layout do gráfico de barras
                fig_trades.update_layout(
                    plot_bgcolor='rgb(40, 40, 40)',  # Fundo escuro
                    paper_bgcolor='rgb(40, 40, 40)',  # Fundo do papel também escuro
                    font=dict(color="white"),  # Cor do texto do gráfico
                    xaxis=dict(
                        color="white",
                        showgrid=False,
                        tickfont=dict(size=12, weight="bold", color="white"),  # Negrito no eixo X
                    ),
                    yaxis=dict(
                        color="white",
                        showgrid=True,
                        gridcolor='rgb(60, 60, 60)',  # Cor da grade
                        tickfont=dict(size=12, weight="bold", color="white"),  # Negrito no eixo Y
                    ),
                    showlegend=False,  # Desativa legenda
                    height=250,  # Altura ajustada
                    margin=dict(t=20, b=40)
                )

                # Exibindo o gráfico de barras
                st.plotly_chart(fig_trades)


                # Criando o DataFrame para o gráfico de pizza
                trade_data_pizza = {
                    "Tipo": ["Gain", "Loss", "Draw"],
                    "Número de Trades": [num_gain, num_loss, num_draw],
                    "Cor": ["green", "red", "blue"],
                }

                trade_df_filtrado_pizza = pd.DataFrame(trade_data_pizza)

                # Gráfico de Pizza
                fig_pizza = go.Figure(go.Pie(
                    labels=trade_df_filtrado_pizza["Tipo"],  # Rótulos (Gain, Loss, Draw)
                    values=trade_df_filtrado_pizza["Número de Trades"],  # Valores de cada categoria
                    marker=dict(colors=trade_df_filtrado_pizza["Cor"]),  # Cores personalizadas
                    textinfo='percent+label',  # Mostrar porcentagem e rótulo
                    insidetextorientation='radial',  # Texto dentro da pizza
                    textfont=dict(size=14, family="Arial, sans-serif", weight="bold")  # Negrito apenas nos valores
                ))

                # Ajustando o layout do gráfico de pizza
                fig_pizza.update_layout(
                    plot_bgcolor='rgb(40, 40, 40)',  # Fundo escuro
                    paper_bgcolor='rgb(40, 40, 40)',  # Fundo do papel também escuro
                    font=dict(color="white"),  # Cor do texto do gráfico
                    height=250,  # Altura ajustada
                    margin=dict(t=20, b=40),  # Margem superior e inferior ajustada para evitar cortes
                    showlegend=False  # Remover a legenda da lateral
                )

                # Exibindo o gráfico de pizza
                st.plotly_chart(fig_pizza)




                # Gráfico de média de Gain e Loss
                with col2:
                    st.markdown("<h3>Média de Gain e Loss</h3>", unsafe_allow_html=True)

                    # Dados para o gráfico de média de Gain e Loss
                    gain_loss_data = {
                        "Tipo": ["Média Gain", "Média Loss"],
                        "Valor": [
                            round(avg_gain, 2) if not pd.isna(avg_gain) else 0,
                            round(abs(avg_loss), 2) if not pd.isna(avg_loss) else 0  # Absoluto para Loss
                        ],
                        "Cor": ["green", "red"],  # Verde para Gain, Vermelho para Loss
                    }

                    gain_loss_df_filtrado = pd.DataFrame(gain_loss_data)

                    # Função para formatar os valores numéricos com separadores
                    def format_value(value):
                        formatted_value = f"R$ {value:,.2f}"
                        return formatted_value.replace(",", "#").replace(".", ",").replace("#", ".")

                    # Função para definir o texto dentro ou fora das barras
                    def get_textposition(value):
                        if value > 50:  # Ajuste esse valor de acordo com suas necessidades
                            return "inside"
                        else:
                            return "outside"

                    # Função para determinar a cor do texto (preto ou branco)
                    def get_textcolor(bar_color):
                        if bar_color in ['#00FF00', '#0000FF']:
                            return 'black'
                        else:
                            return 'white'

                    # Criando o gráfico com Plotly
                    fig_gain_loss = go.Figure(go.Bar(
                        x=gain_loss_df_filtrado["Tipo"],
                        y=gain_loss_df_filtrado["Valor"],
                        marker=dict(color=gain_loss_df_filtrado["Cor"]),
                        text=[format_value(v) for v in gain_loss_df_filtrado["Valor"]],
                        textposition=[get_textposition(v) for v in gain_loss_df_filtrado["Valor"]],
                        textfont=dict(color=[get_textcolor(c) for c in gain_loss_df_filtrado["Cor"]],
                                    size=12, family="Arial, sans-serif", weight="bold"),  # Ajuste no tamanho da fonte
                        textangle=0,  # Texto horizontal
                        width=0.5
                    ))

                    # Ajustando o layout do gráfico para evitar cortes
                    fig_gain_loss.update_layout(
                        plot_bgcolor='rgb(40, 40, 40)',  # Fundo escuro
                        paper_bgcolor='rgb(40, 40, 40)',  # Fundo do papel também escuro
                        font=dict(color="white", family="Arial, sans-serif", weight="bold"),  # Texto normal
                        xaxis=dict(
                            color="white",
                            showgrid=False,
                            title_font=dict(size=14, family="Arial, sans-serif", weight="bold")  # Título do eixo X sem negrito
                        ),
                        yaxis=dict(
                            color="white",
                            showgrid=True,
                            gridcolor='rgb(60, 60, 60)',  # Cor da grade
                            title_font=dict(size=14, family="Arial, sans-serif", weight="bold")  # Título do eixo Y sem negrito
                        ),
                        showlegend=False,  # Desativa legenda
                        height=250,  # Altura ajustada
                        margin=dict(t=20, b=40)  # Margem superior e inferior ajustada para evitar cortes
                    )

                    # Exibindo o gráfico
                    st.plotly_chart(fig_gain_loss)




            with col2:
                #st.markdown("<h3>Média de Gain e Loss</h3>", unsafe_allow_html=True)
                # Dados para o gráfico de média de Gain e Loss
                gain_loss_data = {
                    "Tipo": ["Média Gain", "Média Loss"],
                    "Valor": [
                        round(avg_gain, 2) if not pd.isna(avg_gain) else 0,
                        round(abs(avg_loss), 2) if not pd.isna(avg_loss) else 0  # Absoluto para Loss
                    ],
                    "Cor": ["green", "red"],  # Verde para Gain, Vermelho para Loss
                }

                gain_loss_df_filtrado = pd.DataFrame(gain_loss_data)

                # Gráfico de Pizza
                fig_pizza_gain_loss = go.Figure(go.Pie(
                    labels=gain_loss_df_filtrado["Tipo"],  # Rótulos (Média Gain, Média Loss)
                    values=gain_loss_df_filtrado["Valor"],  # Valores de cada categoria
                    marker=dict(colors=gain_loss_df_filtrado["Cor"]),  # Cores personalizadas
                    textinfo='percent+label',  # Mostrar porcentagem e rótulo
                    insidetextorientation='radial',  # Texto dentro da pizza
                    textfont=dict(size=14, family="Arial, sans-serif", weight="bold")  # Negrito apenas nos valores
                ))

                # Ajustando o layout do gráfico de pizza
                fig_pizza_gain_loss.update_layout(
                    plot_bgcolor='rgb(40, 40, 40)',  # Fundo escuro
                    paper_bgcolor='rgb(40, 40, 40)',  # Fundo do papel também escuro
                    font=dict(color="white"),  # Cor do texto do gráfico
                    height=250,  # Altura ajustada
                    margin=dict(t=20, b=40),  # Margem superior e inferior ajustada para evitar cortes
                    showlegend=False  # Remover a legenda da lateral
                )

                # Exibindo o gráfico de pizza
                st.plotly_chart(fig_pizza_gain_loss)




                # Função para formatar os valores numéricos com separadores de milhar e casas decimais
                def format_value(value):
                    formatted_value = f"R$ {value:,.2f}"
                    return formatted_value.replace(",", "#").replace(".", ",").replace("#", ".")

                # Gráfico de Melhor Trade e Pior Trade
                with col3:
                    st.markdown("<h3>Melhor e Pior Trade</h3>", unsafe_allow_html=True)

                    # Dados para o gráfico de Melhor Trade e Pior Trade
                    best_worst_data = {
                        "Tipo": ["Melhor Trade", "Pior Trade"],
                        "Valor": [round(best_trade, 2) if not pd.isna(best_trade) else 0,
                                round(abs(worst_trade), 2) if not pd.isna(worst_trade) else 0],  # Número absoluto para o pior trade
                        "Cor": ["green", "red"],  # Verde para Melhor, Vermelho para Pior
                    }

                    best_worst_df_filtrado = pd.DataFrame(best_worst_data)

                    # Função para definir o texto dentro ou fora das barras
                    def get_textposition(value):
                        if value > 50:  # Ajuste esse valor de acordo com suas necessidades
                            return "inside"
                        else:
                            return "outside"

                    # Função para determinar a cor do texto (preto ou branco)
                    def get_textcolor(bar_color):
                        if bar_color in ['#00FF00', '#0000FF']:  # Cores claras
                            return 'black'
                        else:  # Cores escuras
                            return 'white'

                    # Criando o gráfico com Plotly
                    fig_best_worst = go.Figure(go.Bar(
                        x=best_worst_df_filtrado["Tipo"],
                        y=best_worst_df_filtrado["Valor"],
                        marker=dict(color=best_worst_df_filtrado["Cor"]),
                        text=[format_value(v) for v in best_worst_df_filtrado["Valor"]],  # Formatando com separadores
                        textposition=[get_textposition(v) for v in best_worst_df_filtrado["Valor"]],
                        textfont=dict(color=[get_textcolor(c) for c in best_worst_df_filtrado["Cor"]],
                                    size=12, family="Arial, sans-serif", weight="bold"),  # Tamanho da fonte ajustado
                        textangle=0,  # Texto horizontal
                        width=0.5
                    ))

                    # Ajustando o layout do gráfico para manter a consistência com o estilo do gráfico anterior
                    fig_best_worst.update_layout(
                        plot_bgcolor='rgb(40, 40, 40)',  # Fundo escuro
                        paper_bgcolor='rgb(40, 40, 40)',  # Fundo do papel também escuro
                        font=dict(color="white", family="Arial, sans-serif", weight="bold"),  # Texto em branco e em negrito
                        xaxis=dict(
                            color="white",
                            showgrid=False,
                            title_font=dict(size=14, family="Arial, sans-serif", weight="bold")  # Título do eixo X em negrito
                        ),
                        yaxis=dict(
                            color="white",
                            showgrid=True,
                            gridcolor='rgb(60, 60, 60)',  # Cor da grade
                            title_font=dict(size=14, family="Arial, sans-serif", weight="bold")  # Título do eixo Y em negrito
                        ),
                        showlegend=False,  # Desativa legenda
                        height=250,  # Altura ajustada
                        margin=dict(t=20, b=40)  # Margem superior e inferior ajustada para evitar cortes
                    )

                    # Exibindo o gráfico
                    st.plotly_chart(fig_best_worst)





            with col3:
                # Dados para o gráfico de Melhor Trade e Pior Trade
                best_worst_data = {
                    "Tipo": ["Melhor Trade", "Pior Trade"],
                    "Valor": [
                        round(best_trade, 2) if not pd.isna(best_trade) else 0,
                        round(abs(worst_trade), 2) if not pd.isna(worst_trade) else 0  # Número absoluto para o pior trade
                    ],
                    "Cor": ["green", "red"],  # Verde para Melhor, Vermelho para Pior
                }

                best_worst_df_filtrado = pd.DataFrame(best_worst_data)

                # Gráfico de Pizza
                fig_pizza_best_worst = go.Figure(go.Pie(
                    labels=best_worst_df_filtrado["Tipo"],  # Rótulos (Melhor Trade, Pior Trade)
                    values=best_worst_df_filtrado["Valor"],  # Valores de cada categoria
                    marker=dict(colors=best_worst_df_filtrado["Cor"]),  # Cores personalizadas
                    textinfo='percent+label',  # Mostrar porcentagem e rótulo
                    insidetextorientation='radial',  # Texto dentro da pizza
                    textfont=dict(size=14, family="Arial, sans-serif", weight="bold")  # Negrito apenas nos valores
                ))

                # Ajustando o layout do gráfico de pizza
                fig_pizza_best_worst.update_layout(
                    plot_bgcolor='rgb(40, 40, 40)',  # Fundo escuro
                    paper_bgcolor='rgb(40, 40, 40)',  # Fundo do papel também escuro
                    font=dict(color="white"),  # Cor do texto do gráfico
                    height=250,  # Altura ajustada
                    margin=dict(t=20, b=40),  # Margem superior e inferior ajustada para evitar cortes
                    showlegend=False  # Remover a legenda da lateral
                )

                # Exibindo o gráfico de pizza
                st.plotly_chart(fig_pizza_best_worst)




                # Gráfico de Patrimônio
                with col4:
                    # Gráfico de Patrimônio
                    st.markdown("<h3>Gráfico de Patrimônio</h3>", unsafe_allow_html=True)

                    # Calculando o resultado acumulado
                    # Soma cumulativa dos resultados por operação
                    df_filtrado["Resultado Acumulado"] = df_filtrado["R$"].cumsum()

                    # Criando o gráfico de linha
                    fig_patrimonio = go.Figure()

                    # Adicionando a linha preenchida
                    fig_patrimonio.add_trace(go.Scatter(
                        x=df_filtrado["Data"],  # Eixo X: Data da operação
                        y=df_filtrado["Resultado Acumulado"],  # Eixo Y: Resultado acumulado
                        mode="lines",  # Linha contínua
                        fill="tozeroy",  # Preencher para o eixo Y
                        # Preenchimento com degradê vermelho abaixo de zero e verde acima de zero
                        fillcolor="rgba(255, 0, 0, 0.3)" if df_filtrado["Resultado Acumulado"].iloc[-1] < 0 else "rgba(0, 255, 0, 0.3)",
                        line=dict(color="rgb(255, 0, 0)" if df_filtrado["Resultado Acumulado"].iloc[-1] < 0 else "rgb(0, 255, 0)"),  # Cor da linha
                        name="Resultado Acumulado",
                    ))

                    # Ajustando o layout do gráfico para manter o estilo dark mode
                    fig_patrimonio.update_layout(
                        plot_bgcolor='rgb(40, 40, 40)',  # Fundo escuro
                        paper_bgcolor='rgb(40, 40, 40)',  # Fundo do papel também escuro
                        font=dict(color="white"),  # Cor do texto do gráfico
                        xaxis=dict(
                            #title="Data",
                            title_font=dict(size=16, family="Arial, sans-serif", weight='bold'),  # Título do eixo X em negrito
                            color="white",
                            showgrid=False,
                            tickfont=dict(size=14, family="Arial, sans-serif", weight='bold')  # Valores do eixo X em negrito
                        ),
                        yaxis=dict(
                            #title="Patrimônio Acumulado (R$)",
                            title_font=dict(size=16, family="Arial, sans-serif", weight='bold'),  # Título do eixo Y em negrito
                            color="white",
                            showgrid=True,
                            gridcolor='rgb(60, 60, 60)',  # Cor da grade
                            tickfont=dict(size=14, family="Arial, sans-serif", weight='bold')  # Valores do eixo Y em negrito
                        ),
                        height=515,  # Altura ajustada
                        margin=dict(t=20, b=40)
                    )

                    # Exibindo o gráfico
                    st.plotly_chart(fig_patrimonio)




            # Criando colunas para os gráficos lado a lado
            col1, col2 = st.columns(2)

            # Gráfico de Resultado por Setup
            with col1:
                st.markdown("<h3>Resultado por Setup</h3>", unsafe_allow_html=True)

                # Calculando o resultado por setup
                result_por_setup = df_filtrado.groupby("Setup")["R$"].sum().reset_index()

                # Adicionando a cor com base no resultado
                result_por_setup["Cor"] = result_por_setup["R$"].apply(
                    lambda x: "green" if x > 0 else "red")  # Verde se positivo, Vermelho se negativo

                # Função para formatar os valores numéricos com separadores de milhar e casas decimais
                def format_value(value):
                    formatted_value = f"R$ {value:,.2f}"
                    return formatted_value.replace(",", "#").replace(".", ",").replace("#", ".")

                # Função para definir a cor do texto com base na cor da barra
                def text_color(cor):
                    if cor == "#00FF00":  # Verde
                        return "black"  # Texto em preto para barras verdes
                    else:
                        return "white"  # Texto em branco para barras vermelhas

                # Criando o gráfico com Plotly
                fig_result_por_setup = go.Figure(go.Bar(
                    y=result_por_setup["Setup"],  # Eixo Y para barras horizontais
                    x=result_por_setup["R$"],  # Resultado no eixo X
                    marker=dict(color=result_por_setup["Cor"]),
                    # Formatar com 2 casas decimais
                    text=[format_value(v) for v in result_por_setup["R$"]],
                    textposition="inside",  # Posiciona os textos dentro das barras
                    textfont=dict(
                        size=14, 
                        family="Arial, sans-serif", 
                        weight='bold', 
                        color=[text_color(cor) for cor in result_por_setup["Cor"]]  # Define a cor do texto dinamicamente
                    ),
                    orientation="h",  # Define a orientação horizontal
                ))

                # Ajustando o layout do gráfico para evitar cortes e manter o estilo dark mode
                fig_result_por_setup.update_layout(
                    plot_bgcolor='rgb(40, 40, 40)',  # Fundo escuro
                    paper_bgcolor='rgb(40, 40, 40)',  # Fundo do papel também escuro
                    font=dict(color="white"),  # Cor do texto do gráfico
                    xaxis=dict(
                        color="white",
                        showgrid=True,
                        gridcolor='rgb(60, 60, 60)',  # Cor da grade
                        tickformat='.2f',  # Formato de exibição dos ticks
                        tickfont=dict(size=14, family="Arial, sans-serif", weight='bold'),  # Valores do eixo X em negrito
                        title_font=dict(size=16, family="Arial, sans-serif", weight='bold'),  # Eixo X em negrito
                    ),
                    yaxis=dict(
                        color="white",
                        showgrid=False,
                        tickfont=dict(size=14, family="Arial, sans-serif", weight='bold'),  # Valores do eixo Y em negrito
                        title_font=dict(size=16, family="Arial, sans-serif", weight='bold'),  # Eixo Y em negrito
                    ),
                    showlegend=False,  # Desativa legenda
                    height=400,  # Altura ajustada
                    margin=dict(t=20, b=40, l=100)  # Margens ajustadas para evitar cortes
                )

                # Exibindo o gráfico
                st.plotly_chart(fig_result_por_setup)




            # Gráfico de Resultado por Ativo
            with col2:
                st.markdown("<h3>Resultado por Ativo</h3>", unsafe_allow_html=True)

                # Calculando o resultado por ativo
                result_por_ativo = df_filtrado.groupby("Ativo")["R$"].sum().reset_index()

                # Adicionando a cor com base no resultado
                result_por_ativo["Cor"] = result_por_ativo["R$"].apply(
                    lambda x: "green" if x > 0 else "red")  # Verde se positivo, Vermelho se negativo

                # Função para formatar os valores numéricos com separadores de milhar e casas decimais
                def format_value(value):
                    formatted_value = f"R$ {value:,.2f}"
                    return formatted_value.replace(",", "#").replace(".", ",").replace("#", ".")

                # Criando o gráfico com Plotly
                fig_result_por_ativo = go.Figure(go.Bar(
                    x=result_por_ativo["Ativo"],
                    y=result_por_ativo["R$"],
                    marker=dict(color=result_por_ativo["Cor"]),
                    # Formatar com 2 casas decimais
                    text=[format_value(v) for v in result_por_ativo["R$"]],
                    textposition="outside",  # Posiciona os textos fora das barras
                    textfont=dict(color='white', size=14, family="Arial, sans-serif", weight='bold'),  # Texto em negrito
                    # Ajuste de largura das barras (0.1 a 1.0, sendo 1 a largura total)
                    width=0.7
                ))

                # Ajustando o layout do gráfico para evitar cortes e manter o estilo dark mode
                fig_result_por_ativo.update_layout(
                    plot_bgcolor='rgb(40, 40, 40)',  # Fundo escuro
                    paper_bgcolor='rgb(40, 40, 40)',  # Fundo do papel também escuro
                    font=dict(color="white"),  # Cor do texto do gráfico
                    xaxis=dict(
                        color="white",
                        showgrid=False,
                        title_font=dict(size=16, family="Arial, sans-serif", weight='bold'),  # Eixo X em negrito
                        tickfont=dict(size=14, family="Arial, sans-serif", weight='bold'),  # Valores do eixo X em negrito
                    ),
                    yaxis=dict(
                        color="white",
                        showgrid=True,
                        gridcolor='rgb(60, 60, 60)',  # Cor da grade
                        title_font=dict(size=16, family="Arial, sans-serif", weight='bold'),  # Eixo Y em negrito
                        tickfont=dict(size=14, family="Arial, sans-serif", weight='bold'),  # Valores do eixo Y em negrito
                    ),
                    showlegend=False,  # Desativa legenda
                    height=400,  # Altura ajustada
                    # Margem superior e inferior ajustada para evitar cortes
                    margin=dict(t=20, b=40)
                )

                # Exibindo o gráfico
                st.plotly_chart(fig_result_por_ativo)




            # Criando colunas para os gráficos lado a lado
            col1, col2 = st.columns(2)

            # Gráfico de Resultado por Operação
            with col1:
                # Filtrando apenas os trades com resultados (não-zero)
                df_filtrado_trades = df_filtrado[df_filtrado["R$"] != 0]

                # Gráfico de Resultado por Operação (Gain, Loss e Zero com datas)
                st.markdown("<h3>Resultado por Operação</h3>", unsafe_allow_html=True)

                # Adicionando uma coluna para a cor das barras
                # Verde para Gain (positivo), Vermelho para Loss (negativo), Cinza para Zero
                df_filtrado_trades["Cor Barra"] = df_filtrado_trades["R$"].apply(
                    lambda x: "green" if x > 0 else "red" if x < 0 else "gray")

                # Criando o gráfico de barras com os índices dos trades e o resultado de cada operação
                fig_resultado = go.Figure(go.Bar(
                    # Eixo X: Índices dos trades (cada operação)
                    x=df_filtrado_trades.index,
                    y=df_filtrado_trades["R$"],  # Eixo Y: Resultado da operação (R$)
                    # Definindo as cores das barras
                    marker=dict(color=df_filtrado_trades["Cor Barra"]),
                    # Exibindo o valor de cada barra com 2 casas decimais
                    text=[f"{v:.2f}" for v in df_filtrado_trades["R$"]],
                    textposition="outside",  # Posiciona os textos fora das barras
                    textfont=dict(color='white', size=14, family="Arial, sans-serif"),
                    # Ajustando a largura das barras (0.9 para barras mais largas e próximas)
                    width=0.9,
                ))

                # Ajustando o layout do gráfico para manter o estilo dark mode e reduzir o espaçamento
                fig_resultado.update_layout(
                    plot_bgcolor='rgb(40, 40, 40)',  # Fundo escuro
                    paper_bgcolor='rgb(40, 40, 40)',  # Fundo do papel também escuro
                    font=dict(color="white"),  # Cor do texto do gráfico
                    xaxis=dict(
                        title="",  # Remover o título do eixo X
                        color="white",
                        showgrid=False,
                        showticklabels=False,  # Remover os rótulos (ticks) do eixo X
                    ),
                    yaxis=dict(
                        title="Resultado (R$)",  # Título do eixo Y
                        color="white",
                        showgrid=True,
                        gridcolor='rgb(60, 60, 60)',  # Cor da grade
                    ),
                    showlegend=False,  # Desativa legenda
                    height=400,  # Altura ajustada
                    # Margem superior e inferior ajustada para evitar cortes
                    margin=dict(t=20, b=40),
                )

                # Exibindo o gráfico
                st.plotly_chart(fig_resultado)

            with col2:
                # Gráfico de Patrimônio
                st.markdown("<h3>Gráfico de Patrimônio</h3>", unsafe_allow_html=True)

                # Calculando o resultado acumulado
                # Soma cumulativa dos resultados por operação
                df_filtrado["Resultado Acumulado"] = df_filtrado["R$"].cumsum()

                # Criando o gráfico de linha preenchido
                fig_patrimonio = go.Figure()

                # Adicionando a linha preenchida com cor cinza
                fig_patrimonio.add_trace(go.Scatter(
                    x=df_filtrado["Data"],  # Eixo X: Data da operação
                    y=df_filtrado["Resultado Acumulado"],  # Eixo Y: Resultado acumulado
                    mode="lines",  # Linha contínua
                    fill="tozeroy",  # Preencher para o eixo Y
                    fillcolor="rgba(128,128,128,0.3)",  # Cor cinza para o preenchimento
                    line=dict(color="rgb(105, 105, 105)", width=2),  # Linha cinza escuro
                    name="Resultado Acumulado",
                ))

                # Ajustando o layout do gráfico para manter o estilo dark mode
                fig_patrimonio.update_layout(
                    plot_bgcolor='rgb(40, 40, 40)',  # Fundo escuro
                    paper_bgcolor='rgb(40, 40, 40)',  # Fundo do papel também escuro
                    font=dict(color="white"),  # Cor do texto do gráfico
                    xaxis=dict(
                        #title="Data",
                        color="white",
                        showgrid=False,
                        title_font=dict(size=16, family="Arial, sans-serif", weight='bold'),  # Título do eixo X em negrito
                        tickfont=dict(size=14, family="Arial, sans-serif", weight='bold')  # Valores do eixo X em negrito
                    ),
                    yaxis=dict(
                        #title="Patrimônio Acumulado (R$)",
                        color="white",
                        showgrid=True,
                        gridcolor='rgb(60, 60, 60)',  # Cor da grade
                        title_font=dict(size=16, family="Arial, sans-serif", weight='bold'),  # Título do eixo Y em negrito
                        tickfont=dict(size=14, family="Arial, sans-serif", weight='bold')  # Valores do eixo Y em negrito
                    ),
                    height=400,  # Altura ajustada
                    margin=dict(t=20, b=40)  # Margens ajustadas para evitar cortes
                )

                # Exibindo o gráfico
                st.plotly_chart(fig_patrimonio)   


        # Resultado Mês
        elif selected == "Resultado Mês":
            #st.title("Resultado Mês")

            # Função para calcular as métricas mensais
            def calcular_metricas(df_filtrado):
                df_filtrado['Data'] = pd.to_datetime(df_filtrado['Data'])  # Converte a coluna 'Data' para datetime
                
                # Lista de meses em português
                meses_pt = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
                
                # Extrai o nome do mês da data e traduz para português
                df_filtrado['Mês'] = df_filtrado['Data'].dt.month.apply(lambda x: meses_pt[x - 1])

                # Agrupa por mês e realiza os cálculos
                resultados_mensais = df_filtrado.groupby('Mês').agg(
                    quantidade_trades=('R$', 'size'),
                    num_gain=('Gain/Loss', lambda x: (x == 'Gain').sum()),
                    num_loss=('Gain/Loss', lambda x: (x == 'Loss').sum()),
                    num_draw=('Gain/Loss', lambda x: (x == 'Draw').sum()),
                    total_ganho=('R$', lambda x: x[df_filtrado['Gain/Loss'] == 'Gain'].sum()),
                    total_perda=('R$', lambda x: x[df_filtrado['Gain/Loss'] == 'Loss'].sum())
                )

                # Cálculos adicionais
                resultados_mensais['taxa_acerto'] = (resultados_mensais['num_gain'] / (resultados_mensais['num_gain'] + resultados_mensais['num_loss'])) * 100
                resultados_mensais['média_ganho'] = df_filtrado[df_filtrado['Gain/Loss'] == 'Gain'].groupby('Mês')['R$'].mean()
                resultados_mensais['média_perda'] = df_filtrado[df_filtrado['Gain/Loss'] == 'Loss'].groupby('Mês')['R$'].mean()
                resultados_mensais['risco_retorno'] = resultados_mensais['média_ganho'] / abs(resultados_mensais['média_perda'])
                resultados_mensais['breakeven'] = 100 / (1 + resultados_mensais['risco_retorno'])
                resultados_mensais['fator_lucro'] = resultados_mensais['total_ganho'] / abs(resultados_mensais['total_perda'])
                resultados_mensais['edge'] = resultados_mensais['taxa_acerto'] - resultados_mensais['breakeven']

                # Calcular o Resultado Bruto (Total Ganho - Total Perda)
                resultados_mensais['resultado_bruto'] = resultados_mensais['total_ganho'] + resultados_mensais['total_perda']

                # Ordenar os meses na ordem correta (de Janeiro a Dezembro)
                resultados_mensais = resultados_mensais.reindex(meses_pt)

                # Filtrar para remover os meses sem dados
                resultados_mensais = resultados_mensais.dropna(subset=['quantidade_trades'])

                # Reorganizar as colunas na ordem desejada
                resultados_mensais = resultados_mensais[[
                    'quantidade_trades', 'num_gain', 'num_loss', 'num_draw', 'taxa_acerto',
                    'total_ganho', 'total_perda', 'resultado_bruto', 'média_ganho', 'média_perda',
                    'risco_retorno', 'breakeven', 'fator_lucro', 'edge'
                ]]

                # Formatação dos valores
                resultados_mensais['quantidade_trades'] = resultados_mensais['quantidade_trades'].astype(int)
                resultados_mensais['num_gain'] = resultados_mensais['num_gain'].astype(int)
                resultados_mensais['num_loss'] = resultados_mensais['num_loss'].astype(int)
                resultados_mensais['num_draw'] = resultados_mensais['num_draw'].astype(int)

                resultados_mensais['taxa_acerto'] = resultados_mensais['taxa_acerto'].map(lambda x: f"{x:.2f}%")
                resultados_mensais['fator_lucro'] = resultados_mensais['fator_lucro'].map(lambda x: f"{x:.2f}")
                resultados_mensais['edge'] = resultados_mensais['edge'].map(lambda x: f"{x:.2f}%")
                resultados_mensais['total_ganho'] = resultados_mensais['total_ganho'].map(lambda x: f"R$ {x:,.2f}")
                resultados_mensais['total_perda'] = resultados_mensais['total_perda'].map(lambda x: f"R$ {x:,.2f}")
                resultados_mensais['resultado_bruto'] = resultados_mensais['resultado_bruto'].map(lambda x: f"R$ {x:,.2f}")
                resultados_mensais['risco_retorno'] = resultados_mensais['risco_retorno'].map(lambda x: f"{x:.2f}")
                resultados_mensais['média_ganho'] = resultados_mensais['média_ganho'].map(lambda x: f"R$ {x:,.2f}")
                resultados_mensais['média_perda'] = resultados_mensais['média_perda'].map(lambda x: f"R$ {x:,.2f}")
                resultados_mensais['breakeven'] = resultados_mensais['breakeven'].map(lambda x: f"{x:.2f}%")


        


                # Retorna os resultados mensais com o nome do mês como índice
                return resultados_mensais.reset_index()

            # Função para aplicar estilos no DataFrame
            def aplicar_estilos(df_filtrado):
                # Colunas para aplicar estilos
                colunas_verde = ['num_gain', 'total_ganho', 'média_ganho']
                colunas_vermelho = ['num_loss', 'total_perda', 'média_perda']
                colunas_azul = ['num_draw', 'breakeven']
                colunas_laranja = ['risco_retorno']
                colunas_condicionais = ['resultado_bruto', 'edge']  # Novas colunas para estilo condicional
                
                # Função que define o estilo condicional
                def estilo_condicional(valor, coluna):
                    if pd.isna(valor) or valor == '':
                        return ''  # Sem estilo para valores nulos ou vazios
                    if coluna in colunas_verde:
                        return 'color: lightgreen; font-weight: bold;'
                    if coluna in colunas_vermelho:
                        return 'color: lightcoral; font-weight: bold;'
                    if coluna in colunas_azul:
                        return 'color: lightblue; font-weight: bold;'
                    if coluna in colunas_laranja:
                        return 'color: darkorange; font-weight: bold;'
                    if coluna in colunas_condicionais:
                        valor_num = float(valor.replace('%', '').replace('R$', '').replace(',', '').strip())
                        if valor_num > 0:
                            return 'color: lightgreen; font-weight: bold;'
                        elif valor_num < 0:
                            return 'color: lightcoral; font-weight: bold;'
                    return ''  # Sem estilo para outras colunas

                # Aplica estilos por coluna
                styled_df_filtrado = df_filtrado.style.apply(
                    lambda coluna: [estilo_condicional(valor, coluna.name) for valor in coluna],
                    axis=0
                )
                return styled_df_filtrado


            # Criar a interface com Streamlit
            def main():
                #st.title('Métricas de Resultados Mensais')

                # Calcular as métricas mensais
                resultados_mensais = calcular_metricas(df_filtrado)

                # Exibir a tabela no Streamlit sem o índice numérico
                st.subheader('Acompanhamento por Mês')
                styled_table = aplicar_estilos(resultados_mensais.set_index('Mês'))  # Define o Mês como índice
                st.dataframe(styled_table)

            # Rodar a aplicação Streamlit
            if __name__ == "__main__":
                main()


            # Criando colunas para os gráficos lado a lado
            col1, col2 = st.columns(2)

            # Gráfico de Nº de Trades
            with col1:

                # Função para calcular as métricas mensais
                def calcular_metricas(df):
                    df['Data'] = pd.to_datetime(df['Data'])  # Converte a coluna 'Data' para datetime
                    
                    # Lista de meses em português
                    meses_pt = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                                'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
                    
                    # Extrai o número do mês e o nome do mês em português
                    df['Num_Mês'] = df['Data'].dt.month
                    df['Mês'] = df['Num_Mês'].apply(lambda x: meses_pt[x - 1])

                    # Agrupa por mês e realiza os cálculos
                    resultados_mensais = df.groupby(['Num_Mês', 'Mês']).agg(
                        quantidade_trades=('R$', 'size'),
                        num_gain=('Gain/Loss', lambda x: (x == 'Gain').sum()),
                        num_loss=('Gain/Loss', lambda x: (x == 'Loss').sum()),
                        num_draw=('Gain/Loss', lambda x: (x == 'Draw').sum()),
                        total_gain=('R$', lambda x: x[df['Gain/Loss'] == 'Gain'].sum()),
                        total_loss=('R$', lambda x: x[df['Gain/Loss'] == 'Loss'].sum()),
                    ).reset_index()

                    return resultados_mensais

                # Chamando a função para calcular as métricas mensais
                resultados_mensais = calcular_metricas(df_filtrado)

                # Ordenando os resultados pelo número do mês
                resultados_mensais = resultados_mensais.sort_values(by='Num_Mês')

                # Gráfico do número de trades por mês
                st.markdown("<h3>Número de Trades por Mês</h3>", unsafe_allow_html=True)

                fig_trades_por_mes = go.Figure(go.Bar(
                    x=resultados_mensais['Mês'],  # Meses no eixo X
                    y=resultados_mensais['quantidade_trades'],  # Quantidade de trades no eixo Y
                    text=resultados_mensais['quantidade_trades'],  # Exibe o número de trades nas barras
                    textposition='outside',  # Posição do texto fora da barra
                    textfont=dict(size=12, family="Arial, sans-serif", color="white", weight="bold"),  # Texto das barras em negrito
                    marker=dict(color='rgb(169, 169, 169)'),  # Cor das barras
                ))

                # Ajustando o layout para o gráfico
                fig_trades_por_mes.update_layout(
                    plot_bgcolor='rgb(40, 40, 40)',  # Fundo escuro
                    paper_bgcolor='rgb(40, 40, 40)',  # Fundo do papel escuro
                    font=dict(color="white", family="Arial, sans-serif", weight="bold"),  # Fonte geral em negrito
                    xaxis=dict(
                        title="Mês",  # Título do eixo X
                        color="white",
                        showgrid=False,
                        title_font=dict(size=14, family="Arial, sans-serif", weight="bold"),  # Título do eixo em negrito
                    ),
                    yaxis=dict(
                        title="Número de Trades",
                        color="white",
                        title_font=dict(size=14, family="Arial, sans-serif", weight="bold"),  # Título do eixo em negrito
                        showgrid=True,
                        gridcolor='rgb(60, 60, 60)',  # Cor da grade
                    ),
                    showlegend=False,  # Desativa legenda
                    height=400,  # Altura ajustada
                    margin=dict(t=20, b=40)  # Margens ajustadas
                )

                # Exibindo o gráfico
                st.plotly_chart(fig_trades_por_mes)



            # Gráfico de Nº de Trades
            with col2:

                # Função para calcular as métricas mensais
                def calcular_metricas(df):
                    df['Data'] = pd.to_datetime(df['Data'])  # Converte a coluna 'Data' para datetime

                    # Lista de meses em português
                    meses_pt = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                                'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
                    
                    # Extrai o número do mês e nome do mês
                    df['Mês_Num'] = df['Data'].dt.month  # Número do mês (1 a 12)
                    df['Mês'] = df['Mês_Num'].apply(lambda x: meses_pt[x - 1])  # Nome do mês traduzido

                    # Agrupa por número do mês para manter a ordem cronológica
                    resultados_mensais = df.groupby(['Mês_Num', 'Mês']).agg(
                        quantidade_trades=('R$', 'size'),
                        num_gain=('Gain/Loss', lambda x: (x == 'Gain').sum()),
                        num_loss=('Gain/Loss', lambda x: (x == 'Loss').sum()),
                        num_draw=('Gain/Loss', lambda x: (x == 'Draw').sum()),
                        total_gain=('R$', lambda x: x[df['Gain/Loss'] == 'Gain'].sum()),
                        total_loss=('R$', lambda x: x[df['Gain/Loss'] == 'Loss'].sum()),
                    ).reset_index()

                    # Calculando o resultado líquido de cada mês (total_gain - total_loss)
                    resultados_mensais['Resultado'] = resultados_mensais['total_gain'] + resultados_mensais['total_loss']

                    # Ordenando por número do mês
                    resultados_mensais = resultados_mensais.sort_values(by='Mês_Num')

                    return resultados_mensais

                # Chamando a função para calcular as métricas mensais
                resultados_mensais = calcular_metricas(df_filtrado)

                # Gráfico do resultado bruto por mês
                st.markdown("<h3>Resultado Bruto por Mês</h3>", unsafe_allow_html=True)

                # Definindo a cor das barras (verde para resultado positivo, vermelho para negativo)
                resultados_mensais['Cor'] = resultados_mensais['Resultado'].apply(lambda x: 'green' if x > 0 else 'red')

                # Função para formatar os valores como moeda
                def format_currency(value):
                    formatted_value = f"R$ {abs(value):,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")
                    return formatted_value

                # Criando o gráfico de barras
                fig_resultado_por_mes = go.Figure(go.Bar(
                    x=resultados_mensais['Mês'],  # Meses no eixo X
                    y=resultados_mensais['Resultado'],  # Resultado bruto no eixo Y
                    text=[format_currency(v) for v in resultados_mensais['Resultado']],  # Exibe o resultado formatado nas barras
                    textposition='outside',  # Posição do texto fora da barra
                    textfont=dict(size=12, family="Arial, sans-serif", color="white", weight="bold"),  # Texto em negrito
                    marker=dict(color=resultados_mensais['Cor']),  # Cor das barras (verde ou vermelho)
                ))

                # Ajustando o layout para o gráfico
                fig_resultado_por_mes.update_layout(
                    plot_bgcolor='rgb(40, 40, 40)',  # Fundo escuro
                    paper_bgcolor='rgb(40, 40, 40)',  # Fundo do papel escuro
                    font=dict(color="white", family="Arial, sans-serif", weight="bold"),  # Texto do gráfico em negrito
                    xaxis=dict(
                        title="Mês",  # Título do eixo X
                        color="white",
                        title_font=dict(size=14, family="Arial, sans-serif", weight="bold"),  # Título do eixo em negrito
                        showgrid=False,
                    ),
                    yaxis=dict(
                        title="Resultado Bruto (R$)",  # Título do eixo Y
                        color="white",
                        title_font=dict(size=14, family="Arial, sans-serif", weight="bold"),  # Título do eixo em negrito
                        showgrid=True,
                        gridcolor='rgb(60, 60, 60)',  # Cor da grade
                    ),
                    showlegend=False,  # Desativa legenda
                    height=400,  # Altura ajustada
                    margin=dict(t=20, b=40)  # Margens ajustadas
                )

                # Exibindo o gráfico
                st.plotly_chart(fig_resultado_por_mes)






            # Criando colunas para 2 linha de gráficos
            col1, col2 = st.columns(2)

            # Gráfico Risco Retorno por mês
            with col1:

                # Função para calcular as métricas mensais
                def calcular_metricas(df):
                    df['Data'] = pd.to_datetime(df['Data'])  # Converte a coluna 'Data' para datetime

                    # Lista de meses em português
                    meses_pt = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                                'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
                    
                    # Extrai o número do mês e nome do mês
                    df['Mês_Num'] = df['Data'].dt.month  # Número do mês (1 a 12)
                    df['Mês'] = df['Mês_Num'].apply(lambda x: meses_pt[x - 1])  # Nome do mês traduzido

                    # Agrupa por número do mês para manter a ordem cronológica
                    resultados_mensais = df.groupby(['Mês_Num', 'Mês']).agg(
                        quantidade_trades=('R$', 'size'),
                        num_gain=('Gain/Loss', lambda x: (x == 'Gain').sum()),
                        num_loss=('Gain/Loss', lambda x: (x == 'Loss').sum()),
                        num_draw=('Gain/Loss', lambda x: (x == 'Draw').sum()),
                        total_gain=('R$', lambda x: x[df['Gain/Loss'] == 'Gain'].sum()),
                        total_loss=('R$', lambda x: x[df['Gain/Loss'] == 'Loss'].sum()),
                    ).reset_index()

                    # Calculando médias de ganho e perda
                    resultados_mensais['media_gain'] = resultados_mensais['total_gain'] / resultados_mensais['num_gain']
                    resultados_mensais['media_loss'] = resultados_mensais['total_loss'].abs() / resultados_mensais['num_loss']

                    # Calculando risco/retorno (média ganho / média perda)
                    resultados_mensais['risco_retorno'] = resultados_mensais['media_gain'] / resultados_mensais['media_loss']

                    # Ordenando por número do mês para manter a ordem cronológica
                    resultados_mensais = resultados_mensais.sort_values(by='Mês_Num')

                    return resultados_mensais

                # Chamando a função para calcular as métricas mensais
                resultados_mensais = calcular_metricas(df_filtrado)

                # Gráfico de risco/retorno por mês
                st.markdown("<h3>Risco/Retorno por Mês</h3>", unsafe_allow_html=True)

                # Função para formatar os valores
                def format_risco_retorno(value):
                    return f"{value:,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")

                # Criando o gráfico de barras
                fig_risco_retorno = go.Figure(go.Bar(
                    x=resultados_mensais['Mês'],  # Meses no eixo X
                    y=resultados_mensais['risco_retorno'],  # Risco/Retorno no eixo Y
                    text=[format_risco_retorno(v) for v in resultados_mensais['risco_retorno']],  # Exibe o risco/retorno formatado nas barras
                    textposition='outside',  # Posição do texto fora da barra
                    textfont=dict(size=12, family="Arial, sans-serif", color="white", weight="bold"),  # Texto das barras em negrito
                    marker=dict(color='orange'),  # Cor das barras
                ))

                # Ajustando o layout do gráfico
                fig_risco_retorno.update_layout(
                    plot_bgcolor='rgb(40, 40, 40)',  # Fundo escuro
                    paper_bgcolor='rgb(40, 40, 40)',  # Fundo do papel escuro
                    font=dict(color="white", family="Arial, sans-serif", weight="bold"),  # Fonte geral em negrito
                    xaxis=dict(
                        title="Mês",
                        color="white",
                        title_font=dict(size=14, family="Arial, sans-serif", weight="bold"),  # Título do eixo X em negrito
                        showgrid=False,
                    ),
                    yaxis=dict(
                        title="Risco/Retorno",
                        color="white",
                        title_font=dict(size=14, family="Arial, sans-serif", weight="bold"),  # Título do eixo Y em negrito
                        showgrid=True,
                        gridcolor='rgb(60, 60, 60)',  # Cor da grade
                    ),
                    showlegend=False,  # Desativa legenda
                    height=400,  # Altura ajustada
                    margin=dict(t=20, b=40)  # Margens ajustadas
                )

                # Exibindo o gráfico
                st.plotly_chart(fig_risco_retorno)




            with col2:


                # Calculando o breakeven com base no risco/retorno já existente
                resultados_mensais['Breakeven (%)'] = (1 / (1 + resultados_mensais['risco_retorno'])) * 100

                # Gráfico do breakeven por mês
                st.markdown("<h3>Breakeven (%) por Mês</h3>", unsafe_allow_html=True)

                # Função para formatar valores percentuais
                def format_percent(value):
                    return f"{value:,.2f}%".replace(",", "#").replace(".", ",").replace("#", ".")

                # Criando o gráfico de barras
                fig_breakeven_por_mes = go.Figure(go.Bar(
                    x=resultados_mensais['Mês'],  # Meses no eixo X
                    y=resultados_mensais['Breakeven (%)'],  # Breakeven percentual no eixo Y
                    text=[format_percent(v) for v in resultados_mensais['Breakeven (%)']],  # Exibe o breakeven formatado nas barras
                    textposition='outside',  # Posição do texto fora da barra
                    textfont=dict(size=12, family="Arial, sans-serif", color="white", weight="bold"),  # Texto das barras em negrito
                    marker=dict(color='rgb(102, 194, 255)'),  # Cor das barras
                ))

                # Ajustando o layout para o gráfico
                fig_breakeven_por_mes.update_layout(
                    plot_bgcolor='rgb(40, 40, 40)',  # Fundo escuro
                    paper_bgcolor='rgb(40, 40, 40)',  # Fundo do papel escuro
                    font=dict(color="white", family="Arial, sans-serif", weight="bold"),  # Fonte geral em negrito
                    xaxis=dict(
                        title="Mês",  # Título do eixo X
                        color="white",
                        title_font=dict(size=14, family="Arial, sans-serif", weight="bold"),  # Título do eixo em negrito
                        showgrid=False,
                    ),
                    yaxis=dict(
                        title="Breakeven (%)",  # Título do eixo Y
                        color="white",
                        title_font=dict(size=14, family="Arial, sans-serif", weight="bold"),  # Título do eixo em negrito
                        showgrid=True,
                        gridcolor='rgb(60, 60, 60)',  # Cor da grade
                    ),
                    showlegend=False,  # Desativa legenda
                    height=400,  # Altura ajustada
                    margin=dict(t=20, b=40)  # Margens ajustadas
                )

                # Exibindo o gráfico
                st.plotly_chart(fig_breakeven_por_mes)





        # Resultado por Ativo
        elif selected == "Resultado por Ativo":
            #st.header("Resultado por Ativo")

            # Função para calcular as métricas por ativo
            def calcular_metricas(df_filtrado):
                df_filtrado['Data'] = pd.to_datetime(df_filtrado['Data'])  # Converte a coluna 'Data' para datetime
                
                # Agrupa por ativo e realiza os cálculos
                resultados_ativos = df_filtrado.groupby('Ativo').agg(
                    quantidade_trades=('R$', 'size'),
                    num_gain=('Gain/Loss', lambda x: (x == 'Gain').sum()),
                    num_loss=('Gain/Loss', lambda x: (x == 'Loss').sum()),
                    num_draw=('Gain/Loss', lambda x: (x == 'Draw').sum()),
                    total_ganho=('R$', lambda x: x[df_filtrado['Gain/Loss'] == 'Gain'].sum()),
                    total_perda=('R$', lambda x: x[df_filtrado['Gain/Loss'] == 'Loss'].sum())
                )

                # Cálculos adicionais
                resultados_ativos['taxa_acerto'] = (resultados_ativos['num_gain'] / (resultados_ativos['num_gain'] + resultados_ativos['num_loss'])) * 100
                resultados_ativos['média_ganho'] = df_filtrado[df_filtrado['Gain/Loss'] == 'Gain'].groupby('Ativo')['R$'].mean()
                resultados_ativos['média_perda'] = df_filtrado[df_filtrado['Gain/Loss'] == 'Loss'].groupby('Ativo')['R$'].mean()
                resultados_ativos['risco_retorno'] = resultados_ativos['média_ganho'] / abs(resultados_ativos['média_perda'])
                resultados_ativos['breakeven'] = 100 / (1 + resultados_ativos['risco_retorno'])
                resultados_ativos['fator_lucro'] = resultados_ativos['total_ganho'] / abs(resultados_ativos['total_perda'])
                resultados_ativos['edge'] = resultados_ativos['taxa_acerto'] - resultados_ativos['breakeven']

                # Calcular o Resultado Bruto (Total Ganho - Total Perda)
                resultados_ativos['resultado_bruto'] = resultados_ativos['total_ganho'] + resultados_ativos['total_perda']

                # Reorganizar as colunas na ordem desejada
                resultados_ativos = resultados_ativos[[ 
                    'quantidade_trades', 'num_gain', 'num_loss', 'num_draw', 'taxa_acerto',
                    'total_ganho', 'total_perda', 'resultado_bruto', 'média_ganho', 'média_perda',
                    'risco_retorno', 'breakeven', 'fator_lucro', 'edge'
                ]]

                # Formatação dos valores
                resultados_ativos['quantidade_trades'] = resultados_ativos['quantidade_trades'].astype(int)
                resultados_ativos['num_gain'] = resultados_ativos['num_gain'].astype(int)
                resultados_ativos['num_loss'] = resultados_ativos['num_loss'].astype(int)
                resultados_ativos['num_draw'] = resultados_ativos['num_draw'].astype(int)

                resultados_ativos['taxa_acerto'] = resultados_ativos['taxa_acerto'].map(lambda x: f"{x:.2f}%")
                resultados_ativos['fator_lucro'] = resultados_ativos['fator_lucro'].map(lambda x: f"{x:.2f}")
                resultados_ativos['edge'] = resultados_ativos['edge'].map(lambda x: f"{x:.2f}%")
                resultados_ativos['total_ganho'] = resultados_ativos['total_ganho'].map(lambda x: f"R$ {x:,.2f}")
                resultados_ativos['total_perda'] = resultados_ativos['total_perda'].map(lambda x: f"R$ {x:,.2f}")
                resultados_ativos['resultado_bruto'] = resultados_ativos['resultado_bruto'].map(lambda x: f"R$ {x:,.2f}")
                resultados_ativos['risco_retorno'] = resultados_ativos['risco_retorno'].map(lambda x: f"{x:.2f}")
                resultados_ativos['média_ganho'] = resultados_ativos['média_ganho'].map(lambda x: f"R$ {x:,.2f}")
                resultados_ativos['média_perda'] = resultados_ativos['média_perda'].map(lambda x: f"R$ {x:,.2f}")
                resultados_ativos['breakeven'] = resultados_ativos['breakeven'].map(lambda x: f"{x:.2f}%")

                # Retorna os resultados por ativo
                return resultados_ativos.reset_index()

            # Função para aplicar estilos no DataFrame
            def aplicar_estilos(df_filtrado):
                # Colunas para aplicar estilos
                colunas_verde = ['num_gain', 'total_ganho', 'média_ganho']
                colunas_vermelho = ['num_loss', 'total_perda', 'média_perda']
                colunas_azul = ['num_draw', 'breakeven']
                colunas_laranja = ['risco_retorno']
                colunas_condicionais = ['resultado_bruto', 'edge']  # Novas colunas para estilo condicional
                
                # Função que define o estilo condicional
                def estilo_condicional(valor, coluna):
                    if pd.isna(valor) or valor == '':
                        return ''  # Sem estilo para valores nulos ou vazios
                    if coluna in colunas_verde:
                        return 'color: lightgreen; font-weight: bold;'
                    if coluna in colunas_vermelho:
                        return 'color: lightcoral; font-weight: bold;'
                    if coluna in colunas_azul:
                        return 'color: lightblue; font-weight: bold;'
                    if coluna in colunas_laranja:
                        return 'color: darkorange; font-weight: bold;'
                    if coluna in colunas_condicionais:
                        valor_num = float(valor.replace('%', '').replace('R$', '').replace(',', '').strip())
                        if valor_num > 0:
                            return 'color: lightgreen; font-weight: bold;'
                        elif valor_num < 0:
                            return 'color: lightcoral; font-weight: bold;'
                    return ''  # Sem estilo para outras colunas

                # Aplica estilos por coluna
                styled_df_filtrado = df_filtrado.style.apply(
                    lambda coluna: [estilo_condicional(valor, coluna.name) for valor in coluna],
                    axis=0
                )
                return styled_df_filtrado


            # Criar a interface com Streamlit
            def main():
                #st.title('Métricas de Resultados por Ativo')

                # Calcular as métricas por ativo
                resultados_ativos = calcular_metricas(df_filtrado)

                # Exibir a tabela no Streamlit sem o índice numérico
                st.subheader('Acompanhamento por Ativo')
                styled_table = aplicar_estilos(resultados_ativos.set_index('Ativo'))  # Define o Ativo como índice
                st.dataframe(styled_table)

            # Rodar a aplicação Streamlit
            if __name__ == "__main__":
                main()


            # Criando colunas para os gráficos lado a lado
            col1, col2 = st.columns(2)

            # Gráfico de Nº de Trades por Ativo
            with col1:

                # Função para calcular as métricas por ativo
                def calcular_metricas_por_ativo(df):
                    # Agrupa por ativo e realiza os cálculos
                    resultados_por_ativo = df.groupby('Ativo').agg(
                        quantidade_trades=('R$', 'size'),
                        num_gain=('Gain/Loss', lambda x: (x == 'Gain').sum()),
                        num_loss=('Gain/Loss', lambda x: (x == 'Loss').sum()),
                        num_draw=('Gain/Loss', lambda x: (x == 'Draw').sum()),
                        total_gain=('R$', lambda x: x[df['Gain/Loss'] == 'Gain'].sum()),
                        total_loss=('R$', lambda x: x[df['Gain/Loss'] == 'Loss'].sum()),
                    ).reset_index()

                    return resultados_por_ativo

                # Chamando a função para calcular as métricas por ativo
                resultados_por_ativo = calcular_metricas_por_ativo(df_filtrado)

                # Ordenando os resultados por quantidade de trades (opcional)
                resultados_por_ativo = resultados_por_ativo.sort_values(by='quantidade_trades', ascending=False)

                # Gráfico do número de trades por ativo
                st.markdown("<h3>Número de Trades por Ativo</h3>", unsafe_allow_html=True)

                # Criando o gráfico de barras
                fig_trades_por_ativo = go.Figure(go.Bar(
                    x=resultados_por_ativo['Ativo'],  # Ativos no eixo X
                    y=resultados_por_ativo['quantidade_trades'],  # Quantidade de trades no eixo Y
                    text=resultados_por_ativo['quantidade_trades'],  # Exibe o número de trades nas barras
                    textposition='outside',  # Posição do texto fora da barra
                    textfont=dict(size=12, family="Arial, sans-serif", color="white", weight="bold"),  # Texto das barras em negrito
                    marker=dict(color='rgb(169, 169, 169)'),  # Cor das barras
                ))

                # Ajustando o layout para o gráfico
                fig_trades_por_ativo.update_layout(
                    plot_bgcolor='rgb(40, 40, 40)',  # Fundo escuro
                    paper_bgcolor='rgb(40, 40, 40)',  # Fundo do papel escuro
                    font=dict(color="white", family="Arial, sans-serif", weight="bold"),  # Fonte geral em negrito
                    xaxis=dict(
                        title="Ativo",  # Título do eixo X
                        color="white",
                        title_font=dict(size=14, family="Arial, sans-serif", weight="bold"),  # Título do eixo X em negrito
                        showgrid=False,
                    ),
                    yaxis=dict(
                        title="Número de Trades",
                        color="white",
                        title_font=dict(size=14, family="Arial, sans-serif", weight="bold"),  # Título do eixo Y em negrito
                        showgrid=True,
                        gridcolor='rgb(60, 60, 60)',  # Cor da grade
                    ),
                    showlegend=False,  # Desativa legenda
                    height=400,  # Altura ajustada
                    margin=dict(t=20, b=40)  # Margens ajustadas
                )

                # Exibindo o gráfico
                st.plotly_chart(fig_trades_por_ativo)



            # Gráfico de Resultado Bruto por Ativo
            with col2:

                # Função para calcular as métricas por ativo
                def calcular_metricas_por_ativo(df):
                    # Agrupa por ativo e realiza os cálculos
                    resultados_por_ativo = df.groupby('Ativo').agg(
                        quantidade_trades=('R$', 'size'),
                        num_gain=('Gain/Loss', lambda x: (x == 'Gain').sum()),
                        num_loss=('Gain/Loss', lambda x: (x == 'Loss').sum()),
                        num_draw=('Gain/Loss', lambda x: (x == 'Draw').sum()),
                        total_gain=('R$', lambda x: x[df['Gain/Loss'] == 'Gain'].sum()),
                        total_loss=('R$', lambda x: x[df['Gain/Loss'] == 'Loss'].sum()),
                    ).reset_index()

                    # Calculando o resultado líquido de cada ativo (total_gain - total_loss)
                    resultados_por_ativo['Resultado'] = resultados_por_ativo['total_gain'] + resultados_por_ativo['total_loss']

                    return resultados_por_ativo

                # Chamando a função para calcular as métricas por ativo
                resultados_por_ativo = calcular_metricas_por_ativo(df_filtrado)

                # Ordenando os resultados por resultado líquido
                resultados_por_ativo = resultados_por_ativo.sort_values(by='Resultado', ascending=False)

                # Gráfico do resultado bruto por ativo
                st.markdown("<h3>Resultado Bruto por Ativo</h3>", unsafe_allow_html=True)

                # Função para formatar os valores como moeda (R$ 375,00)
                def formatar_moeda(valor):
                    return f"R$ {valor:,.2f}".replace('.', ',').replace(',', '.', 1)

                # Aplicando o formato de moeda nos valores
                resultados_por_ativo['Resultado Formatado'] = resultados_por_ativo['Resultado'].apply(formatar_moeda)

                # Definindo a cor das barras (verde para resultado positivo, vermelho para negativo)
                resultados_por_ativo['Cor'] = resultados_por_ativo['Resultado'].apply(lambda x: 'green' if x > 0 else 'red')

                # Criando o gráfico de barras
                fig_resultado_por_ativo = go.Figure(go.Bar(
                    x=resultados_por_ativo['Ativo'],  # Ativos no eixo X
                    y=resultados_por_ativo['Resultado'],  # Resultado bruto no eixo Y
                    text=resultados_por_ativo['Resultado Formatado'],  # Exibe o resultado formatado como moeda
                    textposition='outside',  # Posição do texto fora da barra
                    textfont=dict(size=12, family="Arial, sans-serif", color="white", weight="bold"),  # Texto das barras em negrito
                    marker=dict(color=resultados_por_ativo['Cor']),  # Cor das barras (verde ou vermelho)
                ))

                # Ajustando o layout para o gráfico
                fig_resultado_por_ativo.update_layout(
                    plot_bgcolor='rgb(40, 40, 40)',  # Fundo escuro
                    paper_bgcolor='rgb(40, 40, 40)',  # Fundo do papel escuro
                    font=dict(color="white", family="Arial, sans-serif", weight="bold"),  # Fonte geral em negrito
                    xaxis=dict(
                        title="Ativo",  # Título do eixo X
                        color="white",
                        title_font=dict(size=14, family="Arial, sans-serif", weight="bold"),  # Título do eixo X em negrito
                        showgrid=False,
                    ),
                    yaxis=dict(
                        title="Resultado Bruto (R$)",  # Título do eixo Y
                        color="white",
                        title_font=dict(size=14, family="Arial, sans-serif", weight="bold"),  # Título do eixo Y em negrito
                        showgrid=True,
                        gridcolor='rgb(60, 60, 60)',  # Cor da grade
                    ),
                    showlegend=False,  # Desativa legenda
                    height=400,  # Altura ajustada
                    margin=dict(t=20, b=40)  # Margens ajustadas
                )

                # Exibindo o gráfico
                st.plotly_chart(fig_resultado_por_ativo)





            # Criando colunas para 2 linha de gráficos
            col1, col2 = st.columns(2)

            # Gráfico Risco Retorno por Ativo
            with col1:

                # Função para calcular as métricas por ativo
                def calcular_metricas_por_ativo(df):
                    # Agrupa por ativo
                    resultados_por_ativo = df.groupby('Ativo').agg(
                        quantidade_trades=('R$', 'size'),
                        num_gain=('Gain/Loss', lambda x: (x == 'Gain').sum()),
                        num_loss=('Gain/Loss', lambda x: (x == 'Loss').sum()),
                        num_draw=('Gain/Loss', lambda x: (x == 'Draw').sum()),
                        total_gain=('R$', lambda x: x[df['Gain/Loss'] == 'Gain'].sum()),
                        total_loss=('R$', lambda x: x[df['Gain/Loss'] == 'Loss'].sum()),
                    ).reset_index()

                    # Calculando médias de ganho e perda
                    resultados_por_ativo['media_gain'] = resultados_por_ativo['total_gain'] / resultados_por_ativo['num_gain']
                    resultados_por_ativo['media_loss'] = resultados_por_ativo['total_loss'].abs() / resultados_por_ativo['num_loss']

                    # Calculando risco/retorno (média ganho / média perda)
                    resultados_por_ativo['risco_retorno'] = resultados_por_ativo['media_gain'] / resultados_por_ativo['media_loss']

                    return resultados_por_ativo

                # Chamando a função para calcular as métricas por ativo
                resultados_por_ativo = calcular_metricas_por_ativo(df_filtrado)

                # Gráfico de risco/retorno por ativo
                st.markdown("<h3>Risco/Retorno por Ativo</h3>", unsafe_allow_html=True)

                # Formatando os valores de risco/retorno para usar vírgula
                resultados_por_ativo['risco_retorno_formatado'] = resultados_por_ativo['risco_retorno'].apply(
                    lambda x: f"{x:,.2f}".replace('.', ',')
                )

                # Criando o gráfico de barras
                fig_risco_retorno = go.Figure(go.Bar(
                    x=resultados_por_ativo['Ativo'],  # Ativos no eixo X
                    y=resultados_por_ativo['risco_retorno'],  # Risco/Retorno no eixo Y
                    text=resultados_por_ativo['risco_retorno_formatado'],  # Exibe o risco/retorno formatado nas barras
                    textposition='outside',  # Posição do texto fora da barra
                    textfont=dict(size=12, family="Arial, sans-serif", color="white", weight="bold"),  # Texto em negrito
                    marker=dict(color='orange'),  # Cor das barras
                ))

                # Ajustando o layout do gráfico
                fig_risco_retorno.update_layout(
                    plot_bgcolor='rgb(40, 40, 40)',  # Fundo escuro
                    paper_bgcolor='rgb(40, 40, 40)',  # Fundo do papel escuro
                    font=dict(color="white"),  # Cor do texto
                    xaxis=dict(
                        title="<b>Ativo</b>",  # Título do eixo X em negrito
                        color="white",
                        showgrid=False,
                    ),
                    yaxis=dict(
                        title="<b>Risco/Retorno</b>",  # Título do eixo Y em negrito
                        color="white",
                        showgrid=True,
                        gridcolor='rgb(60, 60, 60)',  # Cor da grade
                    ),
                    showlegend=False,  # Desativa legenda
                    height=400,  # Altura ajustada
                    margin=dict(t=20, b=40)  # Margens ajustadas
                )

                # Exibindo o gráfico
                st.plotly_chart(fig_risco_retorno)


            with col2:

                # Calculando o breakeven com base no risco/retorno já existente
                resultados_por_ativo['Breakeven (%)'] = (1 / (1 + resultados_por_ativo['risco_retorno'])) * 100

                # Gráfico do breakeven por ativo
                st.markdown("<h3>Breakeven (%) por Ativo</h3>", unsafe_allow_html=True)

                # Formatando os valores de breakeven para usar vírgula e adicionar o símbolo '%'
                resultados_por_ativo['breakeven_formatado'] = resultados_por_ativo['Breakeven (%)'].apply(
                    lambda x: f"{x:,.2f}".replace('.', ',') + '%'
                )

                # Criando o gráfico de barras
                fig_breakeven_por_ativo = go.Figure(go.Bar(
                    x=resultados_por_ativo['Ativo'],  # Ativos no eixo X
                    y=resultados_por_ativo['Breakeven (%)'],  # Breakeven percentual no eixo Y
                    text=resultados_por_ativo['breakeven_formatado'],  # Exibe o breakeven formatado nas barras
                    textposition='outside',  # Posição do texto fora da barra
                    textfont=dict(size=12, family="Arial, sans-serif", color="white", weight="bold"),  # Texto em negrito
                    marker=dict(color='rgb(102, 194, 255)'),  # Cor das barras
                ))

                # Ajustando o layout para o gráfico
                fig_breakeven_por_ativo.update_layout(
                    plot_bgcolor='rgb(40, 40, 40)',  # Fundo escuro
                    paper_bgcolor='rgb(40, 40, 40)',  # Fundo do papel escuro
                    font=dict(color="white"),  # Cor do texto do gráfico
                    xaxis=dict(
                        title="<b>Ativo</b>",  # Título do eixo X em negrito
                        color="white",
                        showgrid=False,
                    ),
                    yaxis=dict(
                        title="<b>Breakeven (%)</b>",  # Título do eixo Y em negrito
                        color="white",
                        showgrid=True,
                        gridcolor='rgb(60, 60, 60)',  # Cor da grade
                    ),
                    showlegend=False,  # Desativa legenda
                    height=400,  # Altura ajustada
                    margin=dict(t=20, b=40)  # Margens ajustadas
                )

                # Exibindo o gráfico
                st.plotly_chart(fig_breakeven_por_ativo)



        # Resultado por Setup
        elif selected == "Resultado por Estratégia":
            #st.header("Resultado por Setup")

            # Função para calcular as métricas por Setup
            def calcular_metricas_por_setup(df_filtrado):
                df_filtrado['Data'] = pd.to_datetime(df_filtrado['Data'])  # Converte a coluna 'Data' para datetime
                
                # Agrupa por Setup e realiza os cálculos
                resultados_setup = df_filtrado.groupby('Setup').agg(
                    quantidade_trades=('R$', 'size'),
                    num_gain=('Gain/Loss', lambda x: (x == 'Gain').sum()),
                    num_loss=('Gain/Loss', lambda x: (x == 'Loss').sum()),
                    num_draw=('Gain/Loss', lambda x: (x == 'Draw').sum()),
                    total_ganho=('R$', lambda x: x[df_filtrado['Gain/Loss'] == 'Gain'].sum()),
                    total_perda=('R$', lambda x: x[df_filtrado['Gain/Loss'] == 'Loss'].sum())
                )

                # Cálculos adicionais
                resultados_setup['taxa_acerto'] = (resultados_setup['num_gain'] / (resultados_setup['num_gain'] + resultados_setup['num_loss'])) * 100
                resultados_setup['média_ganho'] = df_filtrado[df_filtrado['Gain/Loss'] == 'Gain'].groupby('Setup')['R$'].mean()
                resultados_setup['média_perda'] = df_filtrado[df_filtrado['Gain/Loss'] == 'Loss'].groupby('Setup')['R$'].mean()
                resultados_setup['risco_retorno'] = resultados_setup['média_ganho'] / abs(resultados_setup['média_perda'])
                resultados_setup['breakeven'] = 100 / (1 + resultados_setup['risco_retorno'])
                resultados_setup['fator_lucro'] = resultados_setup['total_ganho'] / abs(resultados_setup['total_perda'])
                resultados_setup['edge'] = resultados_setup['taxa_acerto'] - resultados_setup['breakeven']

                # Calcular o Resultado Bruto (Total Ganho - Total Perda)
                resultados_setup['resultado_bruto'] = resultados_setup['total_ganho'] + resultados_setup['total_perda']

                # Ordenar pelo Setup
                resultados_setup = resultados_setup.sort_index()

                # Filtrar para remover os setups sem dados
                resultados_setup = resultados_setup.dropna(subset=['quantidade_trades'])

                # Reorganizar as colunas na ordem desejada
                resultados_setup = resultados_setup[[ 
                    'quantidade_trades', 'num_gain', 'num_loss', 'num_draw', 'taxa_acerto', 
                    'total_ganho', 'total_perda', 'resultado_bruto', 'média_ganho', 'média_perda',
                    'risco_retorno', 'breakeven', 'fator_lucro', 'edge'
                ]]

                # Formatação dos valores
                resultados_setup['quantidade_trades'] = resultados_setup['quantidade_trades'].astype(int)
                resultados_setup['num_gain'] = resultados_setup['num_gain'].astype(int)
                resultados_setup['num_loss'] = resultados_setup['num_loss'].astype(int)
                resultados_setup['num_draw'] = resultados_setup['num_draw'].astype(int)

                resultados_setup['taxa_acerto'] = resultados_setup['taxa_acerto'].map(lambda x: f"{x:.2f}%")
                resultados_setup['fator_lucro'] = resultados_setup['fator_lucro'].map(lambda x: f"{x:.2f}")
                resultados_setup['edge'] = resultados_setup['edge'].map(lambda x: f"{x:.2f}%")
                resultados_setup['total_ganho'] = resultados_setup['total_ganho'].map(lambda x: f"R$ {x:,.2f}")
                resultados_setup['total_perda'] = resultados_setup['total_perda'].map(lambda x: f"R$ {x:,.2f}")
                resultados_setup['resultado_bruto'] = resultados_setup['resultado_bruto'].map(lambda x: f"R$ {x:,.2f}")
                resultados_setup['risco_retorno'] = resultados_setup['risco_retorno'].map(lambda x: f"{x:.2f}")
                resultados_setup['média_ganho'] = resultados_setup['média_ganho'].map(lambda x: f"R$ {x:,.2f}")
                resultados_setup['média_perda'] = resultados_setup['média_perda'].map(lambda x: f"R$ {x:,.2f}")
                resultados_setup['breakeven'] = resultados_setup['breakeven'].map(lambda x: f"{x:.2f}%")

                return resultados_setup.reset_index()

            # Função para aplicar estilos no DataFrame
            def aplicar_estilos(df_filtrado):
                # Colunas para aplicar estilos
                colunas_verde = ['num_gain', 'total_ganho', 'média_ganho']
                colunas_vermelho = ['num_loss', 'total_perda', 'média_perda']
                colunas_azul = ['num_draw', 'breakeven']
                colunas_laranja = ['risco_retorno']
                colunas_condicionais = ['resultado_bruto', 'edge']  # Novas colunas para estilo condicional
                
                # Função que define o estilo condicional
                def estilo_condicional(valor, coluna):
                    if pd.isna(valor) or valor == '':
                        return ''  # Sem estilo para valores nulos ou vazios
                    if coluna in colunas_verde:
                        return 'color: lightgreen; font-weight: bold;'
                    if coluna in colunas_vermelho:
                        return 'color: lightcoral; font-weight: bold;'
                    if coluna in colunas_azul:
                        return 'color: lightblue; font-weight: bold;'
                    if coluna in colunas_laranja:
                        return 'color: darkorange; font-weight: bold;'
                    if coluna in colunas_condicionais:
                        valor_num = float(valor.replace('%', '').replace('R$', '').replace(',', '').strip())
                        if valor_num > 0:
                            return 'color: lightgreen; font-weight: bold;'
                        elif valor_num < 0:
                            return 'color: lightcoral; font-weight: bold;'
                    return ''  # Sem estilo para outras colunas

                # Aplica estilos por coluna
                styled_df_filtrado = df_filtrado.style.apply(
                    lambda coluna: [estilo_condicional(valor, coluna.name) for valor in coluna],
                    axis=0
                )
                return styled_df_filtrado


            # Criar a interface com Streamlit
            def main():
                #st.title('Métricas de Resultados por Setup')

                # Calcular as métricas por Setup
                resultados_setup = calcular_metricas_por_setup(df_filtrado)

                # Exibir a tabela no Streamlit sem o índice numérico
                st.subheader('Acompanhamento por Setup')
                styled_table = aplicar_estilos(resultados_setup.set_index('Setup'))  # Define o Setup como índice
                st.dataframe(styled_table)

            # Rodar a aplicação Streamlit
            if __name__ == "__main__":
                main()


            # Criando colunas para os gráficos lado a lado
            col1, col2 = st.columns(2)

            # Gráfico de Nº de Trades por Setup
            with col1:

                # Função para calcular as métricas por setup
                def calcular_metricas_por_setup(df):
                    # Agrupa por setup e realiza os cálculos
                    resultados_por_setup = df.groupby('Setup').agg(
                        quantidade_trades=('R$', 'size'),
                        num_gain=('Gain/Loss', lambda x: (x == 'Gain').sum()),
                        num_loss=('Gain/Loss', lambda x: (x == 'Loss').sum()),
                        num_draw=('Gain/Loss', lambda x: (x == 'Draw').sum()),
                        total_gain=('R$', lambda x: x[df['Gain/Loss'] == 'Gain'].sum()),
                        total_loss=('R$', lambda x: x[df['Gain/Loss'] == 'Loss'].sum()),
                    ).reset_index()

                    return resultados_por_setup

                # Chamando a função para calcular as métricas por setup
                resultados_por_setup = calcular_metricas_por_setup(df_filtrado)

                # Ordenando os resultados por quantidade de trades (opcional)
                resultados_por_setup = resultados_por_setup.sort_values(by='quantidade_trades', ascending=False)

                # Gráfico do número de trades por setup
                st.markdown("<h3><b>Número de Trades por Setup</b></h3>", unsafe_allow_html=True)  # Título em negrito

                # Criando o gráfico de barras
                fig_trades_por_setup = go.Figure(go.Bar(
                    x=resultados_por_setup['Setup'],  # Setups no eixo X
                    y=resultados_por_setup['quantidade_trades'],  # Quantidade de trades no eixo Y
                    text=resultados_por_setup['quantidade_trades'],  # Exibe o número de trades nas barras
                    textposition='outside',  # Posição do texto fora da barra
                    textfont=dict(size=12, family="Arial, sans-serif", color="white", weight="bold"),  # Texto em negrito nas barras
                    marker=dict(color='rgb(169, 169, 169)'),  # Cor das barras
                ))

                # Ajustando o layout para o gráfico
                fig_trades_por_setup.update_layout(
                    plot_bgcolor='rgb(40, 40, 40)',  # Fundo escuro
                    paper_bgcolor='rgb(40, 40, 40)',  # Fundo do papel escuro
                    font=dict(color="white", family="Arial, sans-serif", weight="bold"),  # Cor e negrito para o texto do gráfico
                    xaxis=dict(
                        title="<b>Setup</b>",  # Título do eixo X em negrito
                        color="white",
                        showgrid=False,
                        tickfont=dict(weight="bold")  # Ticks do eixo X em negrito
                    ),
                    yaxis=dict(
                        title="<b>Número de Trades</b>",  # Título do eixo Y em negrito
                        color="white",
                        showgrid=True,
                        gridcolor='rgb(60, 60, 60)',  # Cor da grade
                        tickfont=dict(weight="bold")  # Ticks do eixo Y em negrito
                    ),
                    showlegend=False,  # Desativa legenda
                    height=400,  # Altura ajustada
                    margin=dict(t=20, b=40)  # Margens ajustadas
                )

                # Exibindo o gráfico
                st.plotly_chart(fig_trades_por_setup)



                # Gráfico de Resultado Bruto por Setup
                with col2:

                    # Função para calcular as métricas por setup
                    def calcular_metricas_por_setup(df):
                        # Agrupa por setup e realiza os cálculos
                        resultados_por_setup = df.groupby('Setup').agg(
                            quantidade_trades=('R$', 'size'),
                            num_gain=('Gain/Loss', lambda x: (x == 'Gain').sum()),
                            num_loss=('Gain/Loss', lambda x: (x == 'Loss').sum()),
                            num_draw=('Gain/Loss', lambda x: (x == 'Draw').sum()),
                            total_gain=('R$', lambda x: x[df['Gain/Loss'] == 'Gain'].sum()),
                            total_loss=('R$', lambda x: x[df['Gain/Loss'] == 'Loss'].sum()),
                        ).reset_index()

                        # Calculando o resultado líquido de cada setup (total_gain - total_loss)
                        resultados_por_setup['Resultado'] = resultados_por_setup['total_gain'] + resultados_por_setup['total_loss']

                        return resultados_por_setup

                    # Chamando a função para calcular as métricas por setup
                    resultados_por_setup = calcular_metricas_por_setup(df_filtrado)

                    # Ordenando os resultados por resultado líquido
                    resultados_por_setup = resultados_por_setup.sort_values(by='Resultado', ascending=False)

                    # Gráfico do resultado bruto por setup
                    st.markdown("<h3><b>Resultado Bruto por Setup</b></h3>", unsafe_allow_html=True)  # Título em negrito

                    # Definindo a cor das barras (verde para resultado positivo, vermelho para negativo)
                    resultados_por_setup['Cor'] = resultados_por_setup['Resultado'].apply(lambda x: 'green' if x > 0 else 'red')

                    # Criando o gráfico de barras
                    fig_resultado_por_setup = go.Figure(go.Bar(
                        x=resultados_por_setup['Setup'],  # Setups no eixo X
                        y=resultados_por_setup['Resultado'],  # Resultado bruto no eixo Y
                        text=resultados_por_setup['Resultado'].apply(lambda x: f"R$ {x:,.2f}".replace(",", ";").replace(".", ",").replace(";", ".")),  # Formato R$ 623,00
                        textposition='outside',  # Posição do texto fora da barra
                        textfont=dict(size=12, family="Arial, sans-serif", color="white", weight="bold"),  # Texto em negrito nas barras
                        marker=dict(color=resultados_por_setup['Cor']),  # Cor das barras (verde ou vermelho)
                    ))

                    # Ajustando o layout para o gráfico
                    fig_resultado_por_setup.update_layout(
                        plot_bgcolor='rgb(40, 40, 40)',  # Fundo escuro
                        paper_bgcolor='rgb(40, 40, 40)',  # Fundo do papel escuro
                        font=dict(color="white", family="Arial, sans-serif", weight="bold"),  # Cor e negrito para o texto do gráfico
                        xaxis=dict(
                            title="<b>Setup</b>",  # Título do eixo X em negrito
                            color="white",
                            showgrid=False,
                            tickfont=dict(weight="bold")  # Ticks do eixo X em negrito
                        ),
                        yaxis=dict(
                            title="<b>Resultado Bruto (R$)</b>",  # Título do eixo Y em negrito
                            color="white",
                            showgrid=True,
                            gridcolor='rgb(60, 60, 60)',  # Cor da grade
                            tickfont=dict(weight="bold")  # Ticks do eixo Y em negrito
                        ),
                        showlegend=False,  # Desativa legenda
                        height=400,  # Altura ajustada
                        margin=dict(t=20, b=40)  # Margens ajustadas
                    )

                    # Exibindo o gráfico
                    st.plotly_chart(fig_resultado_por_setup)




            # Criando colunas para 2 linha de gráficos
            col1, col2 = st.columns(2)

            # Gráfico Risco Retorno por Setup
            with col1:

                # Função para calcular as métricas por setup
                def calcular_metricas_por_setup(df):
                    # Agrupa por setup
                    resultados_por_setup = df.groupby('Setup').agg(
                        quantidade_trades=('R$', 'size'),
                        num_gain=('Gain/Loss', lambda x: (x == 'Gain').sum()),
                        num_loss=('Gain/Loss', lambda x: (x == 'Loss').sum()),
                        num_draw=('Gain/Loss', lambda x: (x == 'Draw').sum()),
                        total_gain=('R$', lambda x: x[df['Gain/Loss'] == 'Gain'].sum()),
                        total_loss=('R$', lambda x: x[df['Gain/Loss'] == 'Loss'].sum()),
                    ).reset_index()

                    # Calculando médias de ganho e perda
                    resultados_por_setup['media_gain'] = resultados_por_setup['total_gain'] / resultados_por_setup['num_gain']
                    resultados_por_setup['media_loss'] = resultados_por_setup['total_loss'].abs() / resultados_por_setup['num_loss']

                    # Calculando risco/retorno (média ganho / média perda)
                    resultados_por_setup['risco_retorno'] = resultados_por_setup['media_gain'] / resultados_por_setup['media_loss']

                    return resultados_por_setup

                # Chamando a função para calcular as métricas por setup
                resultados_por_setup = calcular_metricas_por_setup(df_filtrado)

                # Gráfico de risco/retorno por setup
                st.markdown("<h3><b>Risco/Retorno por Setup</b></h3>", unsafe_allow_html=True)  # Título em negrito

                # Criando o gráfico de barras
                fig_risco_retorno = go.Figure(go.Bar(
                    x=resultados_por_setup['Setup'],  # Setup no eixo X
                    y=resultados_por_setup['risco_retorno'],  # Risco/Retorno no eixo Y
                    text=resultados_por_setup['risco_retorno'].apply(lambda x: f"{x:,.2f}".replace(",", ";").replace(".", ",").replace(";", ".")),  # Formato 2,21
                    textposition='outside',  # Posição do texto fora da barra
                    textfont=dict(size=12, family="Arial, sans-serif", color="white", weight="bold"),  # Texto em negrito nas barras
                    marker=dict(color='orange'),  # Cor das barras
                ))

                # Ajustando o layout do gráfico
                fig_risco_retorno.update_layout(
                    plot_bgcolor='rgb(40, 40, 40)',  # Fundo escuro
                    paper_bgcolor='rgb(40, 40, 40)',  # Fundo do papel escuro
                    font=dict(color="white", family="Arial, sans-serif", weight="bold"),  # Cor e negrito para o texto do gráfico
                    xaxis=dict(
                        title="<b>Setup</b>",  # Título do eixo X em negrito
                        color="white",
                        showgrid=False,
                        tickfont=dict(weight="bold")  # Ticks do eixo X em negrito
                    ),
                    yaxis=dict(
                        title="<b>Risco/Retorno</b>",  # Título do eixo Y em negrito
                        color="white",
                        showgrid=True,
                        gridcolor='rgb(60, 60, 60)',  # Cor da grade
                        tickfont=dict(weight="bold")  # Ticks do eixo Y em negrito
                    ),
                    showlegend=False,  # Desativa legenda
                    height=400,  # Altura ajustada
                    margin=dict(t=20, b=40)  # Margens ajustadas
                )

                # Exibindo o gráfico
                st.plotly_chart(fig_risco_retorno)


                with col2:

                    # Calculando o breakeven com base no risco/retorno já existente
                    resultados_por_setup['Breakeven (%)'] = (1 / (1 + resultados_por_setup['risco_retorno'])) * 100

                    # Gráfico do breakeven por setup
                    st.markdown("<h3><b>Breakeven (%) por Setup</b></h3>", unsafe_allow_html=True)  # Título em negrito

                    # Formatando os valores para exibir como 31,44%
                    resultados_por_setup['Breakeven (%)'] = resultados_por_setup['Breakeven (%)'].apply(lambda x: f"{x:,.2f}".replace(",", ";").replace(".", ",").replace(";", "."))

                    fig_breakeven_por_setup = go.Figure(go.Bar(
                        x=resultados_por_setup['Setup'],  # Setup no eixo X
                        y=resultados_por_setup['Breakeven (%)'],  # Breakeven percentual no eixo Y
                        text=resultados_por_setup['Breakeven (%)'],  # Exibe o breakeven percentual nas barras
                        textposition='outside',  # Posição do texto fora da barra
                        textfont=dict(size=12, family="Arial, sans-serif", color="white", weight="bold"),  # Texto em negrito nas barras
                        marker=dict(color='rgb(102, 194, 255)'),  # Cor das barras
                    ))

                    # Ajustando o layout do gráfico
                    fig_breakeven_por_setup.update_layout(
                        plot_bgcolor='rgb(40, 40, 40)',  # Fundo escuro
                        paper_bgcolor='rgb(40, 40, 40)',  # Fundo do papel escuro
                        font=dict(color="white", family="Arial, sans-serif", weight="bold"),  # Cor e negrito para o texto do gráfico
                        xaxis=dict(
                            title="<b>Setup</b>",  # Título do eixo X em negrito
                            color="white",
                            showgrid=False,
                            tickfont=dict(weight="bold")  # Ticks do eixo X em negrito
                        ),
                        yaxis=dict(
                            title="<b>Breakeven (%)</b>",  # Título do eixo Y em negrito
                            color="white",
                            showgrid=True,
                            gridcolor='rgb(60, 60, 60)',  # Cor da grade
                            tickfont=dict(weight="bold")  # Ticks do eixo Y em negrito
                        ),
                        showlegend=False,  # Desativa legenda
                        height=400,  # Altura ajustada
                        margin=dict(t=20, b=40)  # Margens ajustadas
                    )

                    # Exibindo o gráfico
                    st.plotly_chart(fig_breakeven_por_setup)



# Iniciar a aplicação Streamlit
if __name__ == "__main__":
    main()
