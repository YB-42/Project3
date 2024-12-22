import requests
from dash import Dash, dcc, html, Input, Output, dash_table
import plotly.graph_objs as go

app = Dash(__name__)

API_KEY = 'F9l7Cxzw92y2SAYGaApOBAE68AoBo8B4'

def get_location_key(city_name):
    location_url = f"http://dataservice.accuweather.com/locations/v1/cities/search?apikey={API_KEY}&q={city_name}"
    try:
        response = requests.get(location_url)
        response.raise_for_status()
        location_data = response.json()
        if location_data:
            return location_data[0]['Key']
    except requests.exceptions.HTTPError:
        return None
    except requests.exceptions.RequestException:
        return None

def get_weather_forecast(location_key, days):
    forecast_url = f"http://dataservice.accuweather.com/forecasts/v1/daily/{days}day/{location_key}?apikey={API_KEY}&language=ru-ru"
    try:
        response = requests.get(forecast_url)
        response.raise_for_status()
        return response.json()['DailyForecasts']
    except requests.exceptions.RequestException:
        return None

app.layout = html.Div([
    html.H1("Погодное приложение"),
    dcc.Input(id='start-city', type='text', placeholder='Введите город отправления'),
    dcc.Input(id='intermediate-cities', type='text', placeholder='Промежуточные точки (через запятую)'),
    dcc.Input(id='end-city', type='text', placeholder='Введите город назначения'),
    dcc.Dropdown(
        id='days-dropdown',
        options=[
            {'label': '1 день', 'value': 1},
            {'label': '3 дня', 'value': 3},
            {'label': '5 дней', 'value': 5}
        ],
        value=3,  # Значение по умолчанию
        clearable=False
    ),
    html.Button('Получить погоду', id='submit-button', n_clicks=0),
    dash_table.DataTable(id='weather-table'),
])


@app.callback(
    Output('weather-table', 'data'),
    Output('weather-table', 'columns'),
    Input('submit-button', 'n_clicks'),
    Input('start-city', 'value'),
    Input('intermediate-cities', 'value'),
    Input('end-city', 'value'),
    Input('days-dropdown', 'value')
)
def update_weather(n_clicks, start_city, intermediate_cities, end_city, days):
    if n_clicks > 0:
        cities = [start_city] + [city.strip() for city in intermediate_cities.split(',')] + [end_city]
        all_forecasts = []

        for city in cities:
            location_key = get_location_key(city)
            if not location_key:
                return [], []  # Возвращаем пустую таблицу в случае ошибки

            forecast_data = get_weather_forecast(location_key, days)
            if not forecast_data:
                return [], []  # Возвращаем пустую таблицу в случае ошибки

            for day in forecast_data:
                all_forecasts.append({
                    'Город': city,
                    'Дата': day['Date'],
                    'Макс. температура (°C)': day['Temperature']['Maximum']['Value'],
                    'Мин. температура (°C)': day['Temperature']['Minimum']['Value'],
                    'Вероятность осадков (%)': day['Day']['PrecipitationProbability'],
                    'Скорость ветра (км/ч)': day['Day']['Wind']['Speed']['Value']
                })

        columns = [
            {'name': 'Город', 'id': 'Город'},
            {'name': 'Дата', 'id': 'Дата'},
            {'name': 'Макс. температура (°C)', 'id': 'Макс. температура (°C)'},
            {'name': 'Мин. температура (°C)', 'id': 'Мин. температура (°C)'},
            {'name': 'Вероятность осадков (%)', 'id': 'Вероятность осадков (%)'},
            {'name': 'Скорость ветра (км/ч)', 'id': 'Скорость ветра (км/ч)'}
        ]

        return all_forecasts, columns

if __name__ == '__main__':
    app.run_server(debug=True)