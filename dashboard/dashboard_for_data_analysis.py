import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, dash_table
import glob
import os
import random
from datetime import datetime


app = Dash(__name__)


app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Ozon Reviews Dashboard</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                font-family: 'Arial', sans-serif;
                background-color: #f0f4f8;
                color: #333;
                margin: 0;
            }
            .header {
                background-color: #2c3e50;
                color: white;
                padding: 20px;
                text-align: center;
                border-bottom: 2px solid #3498db;
            }
            .tabs {
                background-color: #ecf0f1;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 20px;
            }
            .tabs .tab {
                display: inline-block;
                padding: 10px 20px;
                margin: 0 5px;
                cursor: pointer;
                background-color: #bdc3c7;
                color: #2c3e50;
                border-radius: 5px;
                transition: all 0.3s ease;
            }
            .tabs .tab--selected {
                background-color: #3498db;
                color: white;
                font-weight: bold;
            }
            .content {
                padding: 20px;
                max-width: 1200px;
                margin: 0 auto;
            }
            .card {
                background-color: white;
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                padding: 20px;
                margin-bottom: 20px;
            }
            .graph-container {
                margin-top: 20px;
            }
            @media (max-width: 768px) {
                .content {
                    padding: 10px;
                }
                .tabs .tab {
                    padding: 8px 15px;
                    margin: 0 2px;
                }
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""


# Чтение данных
def read_csv_file():
    """Load the most recent cleaned data file"""
    data_files = glob.glob('../data/cleaned_ozon_reviews_*.csv')
    if not data_files:
        raise FileNotFoundError("No cleaned data files found in the data directory")

    # Sort by modification time (newest first)
    latest_file = max(data_files, key=os.path.getmtime)
    print(f"Loading data from {latest_file}")

    # Load the data
    df = pd.read_csv(latest_file, encoding='utf-8-sig')

    # Convert date back to datetime
    df['date'] = pd.to_datetime(df['date'])

    return df


df = read_csv_file()


app.layout = html.Div([
    # Header
    html.Div([
        html.H1("Анализ отзывов Ozon", className='header'),
        html.P("Дашборд для анализа отзывов с Ozon (данные с ноября 2022 по май 2025)",
               style={'textAlign': 'center', 'color': '#ecf0f1', 'marginBottom': '10px'})
    ]),
    # Navigation
    html.Div([
        dcc.Tabs(id='tabs', value='home', className='tabs', children=[
            dcc.Tab(label='Главная', value='home'),
            dcc.Tab(label='Данные', value='data'),
            dcc.Tab(label='EDA', value='eda'),
            dcc.Tab(label='Тренды & Закономерности', value='trends'),
            dcc.Tab(label='Выводы & Рекомендации', value='conclusions')
        ])
    ], style={'padding': '10px'}),
    # Content
    html.Div(id='content', className='content')
])


@app.callback(
    Output('content', 'children'),
    Input('tabs', 'value')
)
def render_content(tab):
    if tab == 'home':
        return html.Div([
            html.Div([
                html.H3("Добро пожаловать!", style={'color': '#2c3e50'}),
                html.P(
                    "Этот дашборд позволяет исследовать отзывы пользователей Ozon, выявлять тренды и принимать обоснованные решения.",
                    style={'color': '#7f8c8d'})
            ], className='card')
        ])

    elif tab == 'data':
        return html.Div([
            html.Div([
                html.H3("Обзор данных", style={'color': '#2c3e50'}),
                dash_table.DataTable(
                    data=df.to_dict('records'),
                    columns=[{'name': i, 'id': i} for i in df.columns],
                    filter_action='native',
                    sort_action='native',
                    page_size=10,
                    style_table={'overflowX': 'auto', 'border': '1px solid #ddd'},
                    style_header={'backgroundColor': '#3498db', 'color': 'white', 'fontWeight': 'bold'},
                    style_cell={'padding': '5px', 'textAlign': 'left'}
                )
            ], className='card'),
            html.Div([
                html.H4("Счётчики", style={'color': '#2c3e50'}),
                html.Ul([
                    html.Li(f"Общее число записей: {len(df)}", style={'marginBottom': '10px'}),
                    html.Li(f"Количество пропусков: {df.isnull().sum().sum()}", style={'marginBottom': '10px'}),
                ])
            ], className='card'),
            html.Div([
                html.H4("Распределение по группам рейтингов", style={'color': '#2c3e50'}),
                dcc.Graph(
                    figure=px.pie(df, names='rating_group', title='Распределение отзывов',
                                  color_discrete_sequence=px.colors.sequential.Blues)
                )
            ], className='card graph-container')
        ])

    elif tab == 'eda':
        return html.Div([
            html.Div([
                html.H3("Первичный анализ данных", style={'color': '#2c3e50'}),
                dcc.Graph(
                    figure=px.histogram(df, x='rating', title='Распределение рейтингов', nbins=5,
                                        color_discrete_sequence=['#3498db'])
                ),
                html.P(f"Средний рейтинг: {df['rating'].mean():.2f}", style={'color': '#7f8c8d'}),
                html.P(f"Средняя длина отзыва: {df['text_length'].mean():.2f} символов", style={'color': '#7f8c8d'}),
                dcc.Graph(
                    figure=px.box(df, y='text_length', title='Распределение длины отзывов',
                                  color_discrete_sequence=['#3498db'])
                )
            ], className='card')
        ])

    elif tab == 'trends':
        return html.Div([
            html.Div([
                html.H3("Тренды и закономерности", style={'color': '#2c3e50'}),
                html.Div([
                    dcc.DatePickerRange(
                        id='date-range',
                        start_date=df['date'].min(),
                        end_date=df['date'].max(),
                        display_format='YYYY-MM-DD',
                        style={'marginBottom': '20px', 'backgroundColor': '#ecf0f1', 'padding': '10px',
                               'borderRadius': '5px'}
                    ),
                    dcc.Dropdown(
                        id='rating-group-filter',
                        options=[{'label': i, 'value': i} for i in df['rating_group'].unique()],
                        value=df['rating_group'].unique().tolist(),
                        multi=True,
                        style={'marginBottom': '20px', 'width': '50%'}
                    )
                ]),
                dcc.Graph(id='trends-graph')
            ], className='card')
        ])

    elif tab == 'conclusions':
        return html.Div([
            html.Div([
                html.H3("Выводы и рекомендации", style={'color': '#2c3e50'}),
                html.Div([
                    html.H4("Ключевые выводы", style={'color': '#2c3e50'}),
                    html.Ul([
                        html.Li("89.9% отзывов имеют рейтинг 5, что указывает на высокий уровень удовлетворенности.",
                                style={'marginBottom': '10px'}),
                        html.Li("Низкие рейтинги (1-2) связаны с более длинными отзывами, описывающими проблемы.",
                                style={'marginBottom': '10px'}),
                        html.Li("Активность пикирует в 18:00-20:00, возможно, из-за вечернего времени.",
                                style={'marginBottom': '10px'}),
                        html.Li("98 анонимных отзывов (6.7%) требуют проверки на боты.",
                                style={'marginBottom': '10px'}),
                    ])
                ], className='card'),
                html.Div([
                    html.H4("Рекомендации", style={'color': '#2c3e50'}),
                    html.Ul([
                        html.Li("Анализировать длинные негативные отзывы для решения проблем.",
                                style={'marginBottom': '10px'}),
                        html.Li("Запускать акции в пиковые часы (18:00-20:00).", style={'marginBottom': '10px'}),
                        html.Li("Проверить анонимных авторов на аномалии.", style={'marginBottom': '10px'}),
                        html.Li("Улучшить сбор данных о pros и cons.", style={'marginBottom': '10px'}),
                    ])
                ], className='card'),
                html.Div([
                    html.H4("Дальнейшие шаги", style={'color': '#2c3e50'}),
                    html.Ul([
                        html.Li("Глубокий анализ текстов с NLP.", style={'marginBottom': '10px'}),
                        html.Li("Сегментация по категориям товаров.", style={'marginBottom': '10px'}),
                        html.Li("Прогнозирование рейтингов.", style={'marginBottom': '10px'}),
                        html.Li("Кластеризация пользователей.", style={'marginBottom': '10px'}),
                    ])
                ], className='card')
            ])
        ])



@app.callback(
    Output('trends-graph', 'figure'),
    Input('date-range', 'start_date'),
    Input('date-range', 'end_date'),
    Input('rating-group-filter', 'value')
)
def update_trends_graph(start_date, end_date, rating_groups):
    filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    if rating_groups:
        filtered_df = filtered_df[filtered_df['rating_group'].isin(rating_groups)]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=filtered_df['date'], y=filtered_df['rating'], mode='markers', marker=dict(color='#3498db'),
                   name='Рейтинг'))
    fig.update_layout(
        title='Тренды рейтингов по датам',
        xaxis_title='Дата',
        yaxis_title='Рейтинг',
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#2c3e50')
    )
    return fig


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)