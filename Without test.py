from dash import Dash, dcc, html, Input, Output
import plotly.graph_objs as go
import requests

app = Dash(__name__)

API_KEY = 'sGeA3vC6fxh3Dz6yrfaAAjnkCngJfkiC'

def get_location_key(city_name):
    location_url = f"http://dataservice.accuweather.com/locations/v1/cities/search?apikey={API_KEY}&q={city_name}"
    try:
        response = requests.get(location_url)
        response.raise_for_status()
        location_data = response.json()
        if location_data:
            return location_data[0]['Key'], location_data[0]['LocalizedName'], location_data[0]['GeoPosition']
    except requests.exceptions.HTTPError:
        print(f"Ошибка при получении данных для: {city_name}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")
        return None


def get_weather_forecast(location_key, days):
    forecast_url = f"http://dataservice.accuweather.com/forecasts/v1/daily/{days}day/{location_key}?apikey={API_KEY}&language=ru-ru"
    try:
        response = requests.get(forecast_url)
        response.raise_for_status()
        return response.json().get('DailyForecasts', [])
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")
        return None


app.layout = html.Div([
    html.H1("Погодное приложение"),
    dcc.Input(id='start-city', type='text', placeholder='Город отправления'),
    dcc.Input(id='intermediate-cities', type='text', placeholder='Промежуточные города'),
    dcc.Input(id='end-city', type='text', placeholder='Город назначения'),
    dcc.Dropdown(
        id='days-dropdown',
        options=[
            {'label': '1 день', 'value': 1},
            {'label': '3 дня', 'value': 3},
            {'label': '7 дней', 'value': 7}
        ],
        value=3,
        clearable=False),
    html.Button('Получить погоду', id='submit-button', n_clicks=0),
    dcc.Graph(id='weather-graph')])


@app.callback(
    Output('weather-graph', 'figure'),
    Input('submit-button', 'n_clicks'),
    Input('start-city', 'value'),
    Input('intermediate-cities', 'value'),
    Input('end-city', 'value'),
    Input('days-dropdown', 'value'))

def update_weather(n_clicks, start_city, intermediate_cities, end_city, days):
    if n_clicks > 0:
        cities = [start_city] + [city.strip() for city in intermediate_cities.split(',') if city.strip()] + [end_city]
        all_forecasts = []

        for city in cities:
            location_data = get_location_key(city)
            if not location_data:
                print(f"Не удалось получить данные для: {city}")
                return go.Figure()

            location_key, city_name, geo_position = location_data
            forecast_data = get_weather_forecast(location_key, days)
            if not forecast_data:
                print(f"Не удалось получить прогноз для: {city}")
                return go.Figure()

            for day in forecast_data:
                all_forecasts.append({
                    'Город': city_name,
                    'Дата': day['Date'],
                    'Макс. температура (°C)': day['Temperature']['Maximum']['Value'],
                    'Мин. температура (°C)': day['Temperature']['Minimum']['Value'],
                    'Вероятность осадков (%)': day['Day']['PrecipitationProbability']})
        fig = go.Figure()

        for city in set(forecast['Город'] for forecast in all_forecasts):
            city_forecasts = [forecast for forecast in all_forecasts if forecast['Город'] == city]
            if not city_forecasts:
                print(f"Нет данных для города: {city}")
                continue
            dates = [forecast['Дата'] for forecast in city_forecasts]
            max_temps = [forecast['Макс. температура (°C)'] for forecast in city_forecasts]
            min_temps = [forecast['Мин. температура (°C)'] for forecast in city_forecasts]
            precip_probs = [forecast['Вероятность осадков (%)'] for forecast in city_forecasts]

            fig.add_trace(go.Scatter(
                x=dates,
                y=max_temps,
                mode='lines+markers',
                name=f'{city} Макс. температура (°C)',
                line=dict(color='red')))
            fig.add_trace(go.Scatter(
                x=dates,
                y=min_temps,
                mode='lines+markers',
                name=f'{city} Мин. температура (°C)',
                line=dict(color='blue')))
            fig.add_trace(go.Scatter(
                x=dates,
                y=precip_probs,
                mode='lines+markers',
                name=f'{city} Вероятность осадков (%)',
                line=dict(color='green', dash='dash')))

        fig.update_layout(
            title='Прогноз погоды',
            xaxis_title='Дата',
            yaxis_title='Температура (°C) и Вероятность осадков (%)',
            legend_title='Параметры',
            hovermode='x unified')
        return fig

if __name__ == '__main__':
    app.run_server(debug=True)
