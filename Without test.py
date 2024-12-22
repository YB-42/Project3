from dash import Dash, dcc, html, Input, Output
import plotly.graph_objs as go
import plotly.express as px
import requests
import pandas as pd

app = Dash(__name__)

API_KEY = 'adgqX60nLfmxHj3TQQazOxgDM0M5359T'

def get_location_key(city_name):
    location_url = f"http://dataservice.accuweather.com/locations/v1/cities/search?apikey={API_KEY}&q={city_name}"
    try:
        response = requests.get(location_url)
        response.raise_for_status()
        location_data = response.json()
        if location_data:
            return location_data[0]['Key'], location_data[0]['LocalizedName'], location_data[0]['GeoPosition']
    except requests.exceptions.HTTPError:
        return None
    except requests.exceptions.RequestException:
        return None

def get_weather_forecast(location_key, days):
    forecast_url = f"http://dataservice.accuweather.com/forecasts/v1/daily/{days}day/{location_key}?apikey={API_KEY}&language=ru-ru"
    try:
        response = requests.get(forecast_url)
        response.raise_for_status()
        return response.json().get('DailyForecasts', [])
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
            {'label': '5 дней', 'value': 5}],
        value=3,
        clearable=False),
    html.Button('Получить погоду', id='submit-button', n_clicks=0),
    dcc.Graph(id='weather-graph'),
    dcc.Graph(id='weather-map')])

@app.callback(
    Output('weather-graph', 'figure'),
    Output('weather-map', 'figure'),
    Input('submit-button', 'n_clicks'),
    Input('start-city', 'value'),
    Input('intermediate-cities', 'value'),
    Input('end-city', 'value'),
    Input('days-dropdown', 'value')
)
def update_weather(n_clicks, start_city, intermediate_cities, end_city, days):
    if n_clicks > 0:
        cities = [start_city] + [city.strip() for city in intermediate_cities.split(',') if city.strip()] + [end_city]
        all_forecasts = []
        locations = []

        for city in cities:
            location_data = get_location_key(city)
            if not location_data:
                print(f"Не удалось получить данные для города: {city}")
                return go.Figure(), go.Figure()

            location_key, city_name, geo_position = location_data
            forecast_data = get_weather_forecast(location_key, days)
            if not forecast_data:
                print(f"Не удалось получить прогноз для города: {city}")
                return go.Figure(), go.Figure()

            for day in forecast_data:
                all_forecasts.append({
                    'Город': city_name,
                    'Дата': day['Date'],
                                        'Макс. температура (°C)': day['Temperature']['Maximum']['Value'],
                    'Мин. температура (°C)': day['Temperature']['Minimum']['Value'],
                    'Вероятность осадков (%)': day['Day']['PrecipitationProbability']})
                locations.append({
                    'Город': city_name,
                    'Широта': geo_position['Latitude'],
                    'Долгота': geo_position['Longitude']})

        fig_weather = go.Figure()

        for city in set(forecast['Город'] for forecast in all_forecasts):
            city_forecasts = [forecast for forecast in all_forecasts if forecast['Город'] == city]
            if not city_forecasts:
                print(f"Нет данных для города: {city}")
                continue
            dates = [forecast['Дата'] for forecast in city_forecasts]
            max_temps = [forecast['Макс. температура (°C)'] for forecast in city_forecasts]
            min_temps = [forecast['Мин. температура (°C)'] for forecast in city_forecasts]
            precip_probs = [forecast['Вероятность осадков (%)'] for forecast in city_forecasts]

            fig_weather.add_trace(go.Scatter(
                x=dates,
                y=max_temps,
                mode='lines+markers',
                name=f'{city} Макс. температура (°C)',
                line=dict(color='red')))
            fig_weather.add_trace(go.Scatter(
                x=dates,
                y=min_temps,
                mode='lines+markers',
                name=f'{city} Мин. температура (°C)',
                line=dict(color='blue')))
            fig_weather.add_trace(go.Scatter(
                x=dates,
                y=precip_probs,
                mode='lines+markers',
                name=f'{city} Вероятность осадков (%)',
                line=dict(color='green', dash='dash')))

        fig_weather.update_layout(
            title='Прогноз погоды',
            xaxis_title='Дата',
            yaxis_title='Температура (°C) и Вероятность осадков (%)',
            legend_title='Параметры',
            hovermode='x unified')

        df_locations = pd.DataFrame(locations)
        fig_map = px.scatter_geo(df_locations,
                                  lat='Широта',
                                  lon='Долгота',
                                  text='Город',
                                  title='Города на карте',
                                  template='plotly',
                                  scope='world')
        return fig_weather, fig_map

if __name__ == '__main__':
    app.run_server(debug=True)

