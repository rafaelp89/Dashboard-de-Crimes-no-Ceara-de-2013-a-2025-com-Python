# 1. Importando as bibliotecas necessárias
import pandas as pd
import dash
from dash import dcc, html, Input, Output
import plotly.express as px

# 2. Carregando e preparando os dados
df = pd.read_excel('crimes2013_a_2025.xlsx', engine='openpyxl')
df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
df.dropna(subset=['Data'], inplace=True)
df['Ano'] = df['Data'].dt.year
opcoes_municipios = sorted(df['Município'].unique())
opcoes_anos = sorted(df['Ano'].unique())

# 3. Inicializando a aplicação Dash
app = dash.Dash(__name__)

# 4. Criando o layout do dashboard
app.layout = html.Div(style={'backgroundColor': '#f0f0f0', 'padding': '20px', 'font-family': 'sans-serif'}, children=[
    html.H1(
        children='Dashboard de Crimes Violentos no Ceará',
        style={'textAlign': 'center', 'color': '#8B0000', 'font-size': '40px'}
    ),
    html.Div(
        children='Análise de dados de crimes letais de 2013 a 2025.',
        style={'textAlign': 'center', 'font-size': '20px',
               'margin-bottom': '20px', 'margin-top': '10px'}
    ),

    html.Div(style={'display': 'flex', 'justify-content': 'space-around', 'margin-bottom': '30px'}, children=[
        html.Div(style={'padding': '20px', 'border': '1px solid #ddd', 'border-radius': '5px', 'text-align': 'center', 'background-color': 'white'}, children=[
            html.H3(id='kpi-total-ocorrencias',
                    style={'color': '#8B0000', 'font-size': '32px', 'margin': '0'}),
            html.P('Total de Ocorrências', style={'margin': '0'})
        ]),
        html.Div(style={'padding': '20px', 'border': '1px solid #ddd', 'border-radius': '5px', 'text-align': 'center', 'background-color': 'white'}, children=[
            html.H3(id='kpi-municipio-destaque',
                    style={'color': '#8B0000', 'font-size': '32px', 'margin': '0'}),
            html.P('Município de Destaque', style={'margin': '0'})
        ]),
        html.Div(style={'padding': '20px', 'border': '1px solid #ddd', 'border-radius': '5px', 'text-align': 'center', 'background-color': 'white'}, children=[
            html.H3(id='kpi-media-idade',
                    style={'color': '#8B0000', 'font-size': '32px', 'margin': '0'}),
            html.P('Média de Idade', style={'margin': '0'})
        ]),
    ]),

    html.Div(style={'display': 'flex', 'gap': '20px', 'justify-content': 'center', 'margin-bottom': '30px'}, children=[
        dcc.Dropdown(id='filtro-municipio', options=[{'label': m, 'value': m}
                     for m in opcoes_municipios], placeholder='Selecione um Município', style={'width': '300px'}),
        dcc.Dropdown(id='filtro-ano', options=[{'label': a, 'value': a}
                     for a in opcoes_anos], placeholder='Selecione um Ano', style={'width': '200px'}),
    ]),

    dcc.Graph(id='grafico-evolucao-crimes'),

    ### NOVO: Adicionando o gráfico de escolaridade ao layout ###
    dcc.Graph(id='grafico-escolaridade'),

    html.Div(style={'display': 'flex'}, children=[
        dcc.Graph(id='grafico-top-municipios', style={'width': '60%'}),
        dcc.Graph(id='grafico-genero', style={'width': '40%'})
    ])
])

# O Callback - O Cérebro do Dashboard


@app.callback(
    ### MUDANÇA: Adicionando o gráfico de escolaridade aos Outputs ###
    [Output('kpi-total-ocorrencias', 'children'),
     Output('kpi-municipio-destaque', 'children'),
     Output('kpi-media-idade', 'children'),
     Output('grafico-evolucao-crimes', 'figure'),
     Output('grafico-top-municipios', 'figure'),
     Output('grafico-genero', 'figure'),
     Output('grafico-escolaridade', 'figure')],  # Novo output
    [Input('filtro-municipio', 'value'),
     Input('filtro-ano', 'value')]
)
def update_all(municipio_selecionado, ano_selecionado):
    df_filtrado = df.copy()
    location_string = " no Ceará"

    if municipio_selecionado:
        df_filtrado = df_filtrado[df_filtrado['Município']
                                  == municipio_selecionado]
        location_string = f" em {municipio_selecionado}"
    if ano_selecionado:
        df_filtrado = df_filtrado[df_filtrado['Ano'] == ano_selecionado]
        if not municipio_selecionado:
            location_string += f" em {ano_selecionado}"
        else:
            location_string += f" de {ano_selecionado}"

    # Cálculos para os KPIs
    total_ocorrencias = len(df_filtrado)
    if not df_filtrado.empty:
        media_idade = round(df_filtrado['Idade'].mean())
        if municipio_selecionado:
            municipio_destaque = municipio_selecionado
        else:
            municipio_destaque = df_filtrado['Município'].mode()[0]
    else:
        media_idade = 0
        municipio_destaque = "N/A"

    # --- Recria os gráficos ---

    # Gráfico de Linha
    df_filtrado['Ano-Mes'] = df_filtrado['Data'].dt.to_period('M').astype(str)
    crimes_por_mes = df_filtrado.groupby(
        'Ano-Mes').size().reset_index(name='Contagem')
    title_linha = f'Evolução do Número de Crimes por Mês{location_string}'
    fig_linha_tempo = px.line(crimes_por_mes, x='Ano-Mes',
                              y='Contagem', title=title_linha, template='plotly_white')
    fig_linha_tempo.update_traces(line_color='red')

    # Gráfico de Barras (Municípios)
    if municipio_selecionado:
        title_barras = f'Contagem de Crimes{location_string}'
        dados_barras = df_filtrado['Município'].value_counts().reset_index()
    else:
        title_barras = f'Top 10 Municípios com Mais Ocorrências{location_string.replace(" no Ceará", "")}'
        dados_barras = df_filtrado['Município'].value_counts().nlargest(
            10).reset_index()
    dados_barras.columns = ['Município', 'Contagem']
    fig_barras_municipios = px.bar(dados_barras, x='Município', y='Contagem',
                                   title=title_barras, template='plotly_white', color_discrete_sequence=['#8B0000'])

    # Gráfico de Pizza (Gênero)
    crimes_por_genero = df_filtrado['Gênero'].value_counts().reset_index()
    crimes_por_genero.columns = ['Gênero', 'Contagem']
    title_pizza = f'Distribuição por Gênero{location_string}'
    fig_pizza_genero = px.pie(crimes_por_genero, names='Gênero', values='Contagem', title=title_pizza, template='plotly_white',
                              color_discrete_map={'Masculino': '#8B0000', 'Feminino': '#B22222', 'Não Informado': '#d3d3d3'})

    ### NOVO: Gráfico de Barras Horizontais (Escolaridade) ###
    dados_escolaridade = df_filtrado['Escolaridade'].value_counts(
    ).reset_index()
    dados_escolaridade.columns = ['Escolaridade', 'Contagem']
    title_escolaridade = f'Distribuição por Escolaridade{location_string}'
    fig_escolaridade = px.bar(
        # Ordena para o gráfico ficar mais bonito
        dados_escolaridade.sort_values(by='Contagem', ascending=True),
        x='Contagem',
        y='Escolaridade',
        orientation='h',  # Define a orientação como horizontal
        title=title_escolaridade,
        template='plotly_white',
        color_discrete_sequence=['#8B0000']
    )

    ### MUDANÇA: Retornando os 7 itens (KPIs + Gráficos) ###
    return total_ocorrencias, municipio_destaque, media_idade, fig_linha_tempo, fig_barras_municipios, fig_pizza_genero, fig_escolaridade


# 5. Rodando o servidor
if __name__ == '__main__':
    app.run(debug=True)
