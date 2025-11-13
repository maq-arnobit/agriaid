import requests
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv

load_dotenv()

class AgriculturalAPIs:
    def __init__(self):
        # Load API keys from .env file
        self.openweather_key = os.getenv('OPENWEATHER_API_KEY', '')
        self.agromonitoring_key = os.getenv('AGROMONITORING_API_KEY', '')
        self.news_key = os.getenv('NEWS_API_KEY', '')

    # ==================== WEATHER APIs ====================

    def get_current_weather(self, city=None, lat=None, lon=None):
        """
        OpenWeatherMap - Free tier: 1,000 calls/day
        Get current weather conditions
        """
        if city:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.openweather_key}&units=metric"
        elif lat and lon:
            url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={self.openweather_key}&units=metric"
        else:
            return None

        try:
            response = requests.get(url)
            data = response.json()

            if response.status_code == 200:
                return {
                    'temperature': data['main']['temp'],
                    'feels_like': data['main']['feels_like'],
                    'humidity': data['main']['humidity'],
                    'pressure': data['main']['pressure'],
                    'description': data['weather'][0]['description'],
                    'wind_speed': data['wind']['speed'],
                    'wind_direction': data['wind']['deg'],
                    'clouds': data['clouds']['all'],
                    'visibility': data.get('visibility', 'N/A'),
                    'sunrise': datetime.fromtimestamp(data['sys']['sunrise']).strftime('%H:%M'),
                    'sunset': datetime.fromtimestamp(data['sys']['sunset']).strftime('%H:%M')
                }
        except Exception as e:
            print(f"Weather API error: {e}")
            return None

    def get_weather_forecast(self, city=None, lat=None, lon=None):
        """
        5-day weather forecast (3-hour intervals)
        """
        if city:
            url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={self.openweather_key}&units=metric"
        elif lat and lon:
            url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={self.openweather_key}&units=metric"
        else:
            return None

        try:
            response = requests.get(url)
            data = response.json()

            if response.status_code == 200:
                forecast = []
                for item in data['list']:
                    forecast.append({
                        'datetime': item['dt_txt'],
                        'temp': item['main']['temp'],
                        'description': item['weather'][0]['description'],
                        'humidity': item['main']['humidity'],
                        'rain_3h': item.get('rain', {}).get('3h', 0),
                        'wind_speed': item['wind']['speed'],
                        'clouds': item['clouds']['all']
                    })
                return forecast
        except Exception as e:
            print(f"Forecast API error: {e}")
            return None

    def get_open_meteo_weather(self, lat, lon):
        """
        Open-Meteo - Completely FREE, no API key needed!
        More detailed agricultural weather data
        """
        url = f"https://api.open-meteo.com/v1/forecast"
        params = {
            'latitude': lat,
            'longitude': lon,
            'current': 'temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m',
            'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,rain_sum,windspeed_10m_max',
            'timezone': 'auto',
            'forecast_days': 7
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            # Extract current weather (new API structure)
            current = data.get('current', {})
            daily = data.get('daily', {})

            # Format current weather
            current_weather = {
                'temperature': current.get('temperature_2m', 'N/A'),
                'humidity': current.get('relative_humidity_2m', 'N/A'),
                'precipitation': current.get('precipitation', 0),
                'windspeed': current.get('wind_speed_10m', 'N/A'),
                'time': current.get('time', 'N/A')
            }

            return {
                'current': current_weather,
                'daily_forecast': daily
            }
        except Exception as e:
            print(f"Open-Meteo error: {e}")
            return None

    # ==================== CROP/SOIL APIs ====================

    def get_soil_data(self, lat, lon):
        """
        Agromonitoring Soil API - Free tier available
        Get soil temperature and moisture
        """
        url = f"http://api.agromonitoring.com/agro/1.0/soil?lat={lat}&lon={lon}&appid={self.agromonitoring_key}"

        try:
            response = requests.get(url)
            data = response.json()

            if response.status_code == 200:
                return {
                    'soil_temp': data.get('t10', 'N/A'),  # Temperature at 10cm depth
                    'soil_moisture': data.get('moisture', 'N/A'),
                    'timestamp': datetime.fromtimestamp(data['dt']).strftime('%Y-%m-%d %H:%M')
                }
        except Exception as e:
            print(f"Soil API error: {e}")
            return None

    def get_ndvi_data(self, polygon_id):
        """
        Agromonitoring NDVI (Normalized Difference Vegetation Index)
        Measures crop health - requires polygon ID
        """
        start_time = int((datetime.now() - timedelta(days=30)).timestamp())
        end_time = int(datetime.now().timestamp())

        url = f"http://api.agromonitoring.com/agro/1.0/ndvi/history?polyid={polygon_id}&start={start_time}&end={end_time}&appid={self.agromonitoring_key}"

        try:
            response = requests.get(url)
            data = response.json()

            if response.status_code == 200:
                ndvi_values = []
                for entry in data:
                    ndvi_values.append({
                        'date': datetime.fromtimestamp(entry['dt']).strftime('%Y-%m-%d'),
                        'ndvi_mean': entry['data']['mean'],
                        'ndvi_max': entry['data']['max'],
                        'ndvi_min': entry['data']['min']
                    })
                return ndvi_values
        except Exception as e:
            print(f"NDVI API error: {e}")
            return None

    def create_polygon(self, name, coordinates):
        """
        Create a polygon for your farm field
        coordinates format: [[[lon1, lat1], [lon2, lat2], ...]]
        """
        polygon = {
            "name": name,
            "geo_json": {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": coordinates
                }
            }
        }

        url = f"http://api.agromonitoring.com/agro/1.0/polygons?appid={self.agromonitoring_key}"

        try:
            response = requests.post(url, json=polygon)
            data = response.json()

            if response.status_code == 201:
                return {
                    'polygon_id': data['id'],
                    'name': data['name'],
                    'area': data['area']
                }
        except Exception as e:
            print(f"Polygon creation error: {e}")
            return None

    def get_soilgrids_data(self, lat, lon):
        """
        SoilGrids API - FREE, no key needed
        Get detailed soil properties
        """
        url = f"https://rest.isric.org/soilgrids/v2.0/properties/query"
        params = {
            'lon': lon,
            'lat': lat,
            'property': ['clay', 'sand', 'silt', 'phh2o', 'soc', 'nitrogen'],
            'depth': ['0-5cm', '5-15cm'],
            'value': 'mean'
        }

        try:
            response = requests.get(url, params=params)
            data = response.json()

            soil_info = {}
            for prop in data['properties']['layers']:
                prop_name = prop['name']
                soil_info[prop_name] = prop['depths'][0]['values']['mean']

            return soil_info
        except Exception as e:
            print(f"SoilGrids error: {e}")
            return None

    # ==================== PEST & DISEASE APIs ====================

    def search_pest_info(self, pest_name):
        """
        iNaturalist API - FREE
        Get pest/insect information and observations
        """
        url = "https://api.inaturalist.org/v1/taxa/autocomplete"
        params = {
            'q': pest_name,
            'rank': 'species,genus'
        }

        try:
            response = requests.get(url, params=params)
            data = response.json()

            if data['results']:
                pest = data['results'][0]
                return {
                    'name': pest['name'],
                    'common_name': pest.get('preferred_common_name', 'N/A'),
                    'observations': pest['observations_count'],
                    'photo': pest.get('default_photo', {}).get('medium_url'),
                    'wikipedia_url': pest.get('wikipedia_url')
                }
        except Exception as e:
            print(f"Pest search error: {e}")
            return None

    def get_pest_observations(self, lat, lon, radius_km=50):
        """
        Get recent pest observations near your location
        """
        url = "https://api.inaturalist.org/v1/observations"
        params = {
            'lat': lat,
            'lng': lon,
            'radius': radius_km,
            'taxon_id': 47158,  # Insecta (insects)
            'quality_grade': 'research',
            'per_page': 10,
            'order_by': 'created_at'
        }

        try:
            response = requests.get(url, params=params)
            data = response.json()

            observations = []
            for obs in data['results']:
                observations.append({
                    'species': obs['taxon']['name'],
                    'common_name': obs['taxon'].get('preferred_common_name', 'Unknown'),
                    'observed_on': obs['observed_on'],
                    'location': obs.get('place_guess', 'Unknown'),
                    'photo': obs['photos'][0]['url'] if obs['photos'] else None
                })

            return observations
        except Exception as e:
            print(f"Observations error: {e}")
            return None

    # ==================== NEWS & INFORMATION APIs ====================

    def get_agricultural_news(self, query="agriculture", country="ph", days=7):
        """
        NewsAPI - Free tier: 100 requests/day
        Get latest agricultural news
        """
        url = "https://newsapi.org/v2/everything"
        from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        params = {
            'apiKey': self.news_key,
            'q': query,
            'language': 'en',
            'sortBy': 'publishedAt',
            'from': from_date,
            'pageSize': 10
        }

        try:
            response = requests.get(url, params=params)
            data = response.json()

            if response.status_code == 200:
                articles = []
                for article in data['articles']:
                    articles.append({
                        'title': article['title'],
                        'description': article['description'],
                        'source': article['source']['name'],
                        'url': article['url'],
                        'published': article['publishedAt'],
                        'image': article.get('urlToImage')
                    })
                return articles
        except Exception as e:
            print(f"News API error: {e}")
            return None

    def get_crop_prices_usda(self, commodity='CORN', year=2024):
        """
        USDA NASS API - FREE
        Get crop prices and statistics (US data, but useful for trends)
        """
        # Note: You need to register for free API key at https://quickstats.nass.usda.gov/api
        url = "http://quickstats.nass.usda.gov/api/api_GET/"
        params = {
            'key': 'your_usda_key',
            'commodity_desc': commodity,
            'year': year,
            'statisticcat_desc': 'PRICE RECEIVED',
            'format': 'JSON'
        }

        try:
            response = requests.get(url, params=params)
            data = response.json()

            if 'data' in data:
                return data['data'][:10]  # Return first 10 records
        except Exception as e:
            print(f"USDA API error: {e}")
            return None

    def search_agricultural_papers(self, query):
        """
        Use RSS feeds from agricultural websites (FREE)
        """
        feeds = [
            'https://www.agriculture.com/feed',
            'https://www.farm-equipment.com/rss',
            'http://www.fao.org/news/rss-feed/en/'
        ]

        # You'll need feedparser: pip install feedparser
        try:
            import feedparser

            articles = []
            for feed_url in feeds:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:3]:
                    articles.append({
                        'title': entry.title,
                        'link': entry.link,
                        'published': entry.get('published', 'N/A')
                    })

            return articles
        except ImportError:
            print("Install feedparser: pip install feedparser")
            return None
        except Exception as e:
            print(f"RSS feed error: {e}")
            return None


# ==================== TESTING ====================
if __name__ == "__main__":
    api = AgriculturalAPIs()

    # Test coordinates for Manila
    lat, lon = 14.5995, 120.9842

    print("=== WEATHER DATA ===")
    weather = api.get_current_weather(city="Manila")
    print(json.dumps(weather, indent=2))

    print("\n=== SOIL DATA ===")
    soil = api.get_soil_data(lat, lon)
    print(json.dumps(soil, indent=2))

    print("\n=== PEST OBSERVATIONS ===")
    pests = api.get_pest_observations(lat, lon)
    print(json.dumps(pests[:2], indent=2))

    print("\n=== AGRICULTURAL NEWS ===")
    news = api.get_agricultural_news(query="rice farming")
    print(json.dumps(news[:2], indent=2))