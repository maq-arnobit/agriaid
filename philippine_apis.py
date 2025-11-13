import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
import json


class PhilippineAgriculturalAPIs:

    def __init__(self):
        pass

    # ==================== WEATHER ====================

    def get_pagasa_weather_forecast(self):
        """
        Get PAGASA weather forecast from RSS feed
        """
        feed_url = "http://bagong.pagasa.dost.gov.ph/rss-feed"

        try:
            feed = feedparser.parse(feed_url)

            forecasts = []
            for entry in feed.entries[:5]:
                forecasts.append({
                    'title': entry.title,
                    'summary': entry.summary if hasattr(entry, 'summary') else entry.description,
                    'published': entry.published,
                    'link': entry.link
                })

            return forecasts
        except Exception as e:
            print(f"PAGASA error: {e}")
            return None

    def get_pagasa_tropical_cyclone_info(self):
        """
        Get tropical cyclone information from PAGASA
        """
        url = "https://bagong.pagasa.dost.gov.ph/tropical-cyclone/severe-weather-bulletin"

        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for active cyclone bulletins
            bulletins = soup.find_all('div', class_='bulletin-item')

            cyclone_info = []
            for bulletin in bulletins[:3]:
                cyclone_info.append({
                    'content': bulletin.get_text(strip=True),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                })

            return cyclone_info if cyclone_info else "No active tropical cyclones"
        except Exception as e:
            print(f"Cyclone info error: {e}")
            return None

    # ==================== CROP PRICES ====================

    def get_da_bantay_presyo(self):
        """
        DA Bantay Presyo - Price monitoring
        Scrape from DA website or use cached data
        """
        # DA Bantay Presyo mobile app data endpoint (if available)
        # Alternatively, scrape from website

        url = "http://www.da.gov.ph/bantay-presyo/"

        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')

            # This is a simplified example - actual implementation depends on site structure
            price_data = {
                'rice': 'Check DA website',
                'corn': 'Check DA website',
                'vegetables': 'Check DA website',
                'note': 'Visit http://www.da.gov.ph/bantay-presyo/ for latest prices'
            }

            return price_data
        except Exception as e:
            print(f"Bantay Presyo error: {e}")
            return None

    def get_market_prices_manual(self):
        """
        Manual database of typical Philippine crop prices
        Update this regularly based on DA reports
        """
        # This should be updated from actual sources
        prices = {
            'last_updated': '2024-11',
            'prices': {
                'rice': {
                    'regular_milled': '45-50 PHP/kg',
                    'well_milled': '50-55 PHP/kg',
                    'premium': '55-65 PHP/kg'
                },
                'corn': {
                    'yellow': '20-25 PHP/kg',
                    'white': '18-23 PHP/kg'
                },
                'vegetables': {
                    'tomato': '60-80 PHP/kg',
                    'eggplant': '40-60 PHP/kg',
                    'cabbage': '30-40 PHP/kg',
                    'onion': '80-120 PHP/kg'
                },
                'fruits': {
                    'banana': '50-70 PHP/kg',
                    'mango': '80-120 PHP/kg',
                    'papaya': '30-50 PHP/kg'
                }
            },
            'source': 'DA Price Monitoring',
            'note': 'Prices vary by region and market'
        }

        return prices

    # ==================== AGRICULTURAL ADVISORIES ====================

    def get_da_advisories(self):
        """
        Get latest advisories from Department of Agriculture
        """
        url = "https://www.da.gov.ph/category/advisories/"

        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')

            advisories = []
            articles = soup.find_all('article', limit=5)

            for article in articles:
                title_tag = article.find('h2') or article.find('h3')
                link_tag = article.find('a')

                if title_tag and link_tag:
                    advisories.append({
                        'title': title_tag.get_text(strip=True),
                        'link': link_tag.get('href'),
                        'source': 'DA Philippines'
                    })

            return advisories
        except Exception as e:
            print(f"DA advisories error: {e}")
            return None

    def get_bpi_plant_quarantine_alerts(self):
        """
        Bureau of Plant Industry - pest and disease alerts
        """
        url = "http://bpi.da.gov.ph/"

        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for news/advisory sections
            alerts = {
                'message': 'Check BPI website for latest plant health advisories',
                'website': 'http://bpi.da.gov.ph/',
                'note': 'BPI provides pest and disease advisories for farmers'
            }

            return alerts
        except Exception as e:
            print(f"BPI error: {e}")
            return None

    # ==================== REGIONAL DATA ====================

    def get_regional_weather(self, region):
        """
        Get region-specific weather information
        Philippine regions: NCR, CAR, I-XIII, BARMM
        """
        region_coords = {
            'NCR': (14.5995, 120.9842),  # Metro Manila
            'CAR': (16.4023, 120.5960),  # Baguio
            'I': (16.0934, 120.3320),  # Ilocos
            'II': (16.9754, 121.8107),  # Cagayan Valley
            'III': (15.4800, 120.7100),  # Central Luzon
            'IV-A': (14.1008, 121.0794),  # CALABARZON
            'IV-B': (13.0563, 121.0543),  # MIMAROPA
            'V': (13.4215, 123.4137),  # Bicol
            'VI': (11.0050, 122.5378),  # Western Visayas
            'VII': (10.3157, 123.8854),  # Central Visayas
            'VIII': (11.2504, 125.0076),  # Eastern Visayas
            'IX': (8.4869, 123.8083),  # Zamboanga
            'X': (8.4542, 124.6319),  # Northern Mindanao
            'XI': (7.0731, 125.6128),  # Davao
            'XII': (6.9214, 124.8458),  # SOCCSKSARGEN
            'XIII': (8.9476, 125.5406),  # Caraga
            'BARMM': (7.2045, 124.2302)  # Bangsamoro
        }

        if region.upper() in region_coords:
            lat, lon = region_coords[region.upper()]

            # Use Open-Meteo for free weather data
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                'latitude': lat,
                'longitude': lon,
                'current_weather': True,
                'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum',
                'timezone': 'Asia/Manila'
            }

            try:
                response = requests.get(url, params=params)
                data = response.json()

                return {
                    'region': region.upper(),
                    'current': data['current_weather'],
                    'forecast': data['daily']
                }
            except Exception as e:
                print(f"Regional weather error: {e}")
                return None
        else:
            return f"Region '{region}' not found. Use: NCR, CAR, I-XIII, BARMM"

    # ==================== CROP CALENDAR ====================

    def get_philippine_crop_calendar(self, crop):
        """
        Philippine-specific crop planting calendar
        Based on typical Philippine agricultural seasons
        """
        crop_calendars = {
            'rice': {
                'wet_season': {
                    'planting': 'June-July',
                    'harvesting': 'October-November',
                    'duration': '120-140 days'
                },
                'dry_season': {
                    'planting': 'December-January',
                    'harvesting': 'April-May',
                    'duration': '110-120 days'
                },
                'varieties': ['PSB Rc82', 'NSIC Rc222', 'NSIC Rc160'],
                'notes': 'Ensure adequate irrigation for dry season'
            },
            'corn': {
                'wet_season': {
                    'planting': 'May-June',
                    'harvesting': 'August-September',
                    'duration': '90-110 days'
                },
                'dry_season': {
                    'planting': 'November-December',
                    'harvesting': 'February-March',
                    'duration': '85-95 days'
                },
                'varieties': ['IPB Var 6', 'Pioneer 30G97', 'Dekalb 9130'],
                'notes': 'Yellow corn for feeds, white corn for food'
            },
            'vegetables': {
                'rainy_season': ['kangkong', 'sitaw', 'talong', 'ampalaya'],
                'dry_season': ['tomato', 'repolyo', 'lettuce', 'carrots'],
                'year_round': ['sili', 'okra', 'kalabasa'],
                'notes': 'Timing varies by specific vegetable and region'
            },
            'banana': {
                'planting': 'Year-round, best during start of rainy season',
                'harvesting': '9-12 months after planting',
                'varieties': ['Lakatan', 'Latundan', 'Saba', 'Cavendish'],
                'notes': 'Requires consistent moisture and drainage'
            }
        }

        crop_lower = crop.lower()
        if crop_lower in crop_calendars:
            return crop_calendars[crop_lower]
        else:
            return {
                'message': f"No calendar data for '{crop}'",
                'available_crops': list(crop_calendars.keys())
            }

    # ==================== PEST & DISEASE (PH-SPECIFIC) ====================

    def get_common_philippine_pests(self, crop=None):
        """
        Common pests and diseases in Philippine agriculture
        """
        pests_database = {
            'rice': {
                'pests': [
                    {
                        'name': 'Rice Black Bug (Scotinophara coarctata)',
                        'symptoms': 'Yellowing and drying of plants',
                        'control': 'Remove weeds, use insecticides, handpick bugs'
                    },
                    {
                        'name': 'Rice Tungro Disease',
                        'symptoms': 'Yellow-orange leaves, stunted growth',
                        'control': 'Plant resistant varieties, control leafhoppers'
                    },
                    {
                        'name': 'Rice Blast (Pyricularia oryzae)',
                        'symptoms': 'Diamond-shaped lesions on leaves',
                        'control': 'Use resistant varieties, apply fungicides'
                    }
                ],
                'prevention': 'Use certified seeds, proper spacing, balanced fertilization'
            },
            'corn': {
                'pests': [
                    {
                        'name': 'Corn Borer (Ostrinia furnacalis)',
                        'symptoms': 'Holes in leaves, broken tassels',
                        'control': 'Bt corn varieties, early planting, crop rotation'
                    },
                    {
                        'name': 'Fall Armyworm (Spodoptera frugiperda)',
                        'symptoms': 'Irregular holes in leaves, damaged whorl',
                        'control': 'Scout regularly, use appropriate insecticides'
                    }
                ],
                'prevention': 'Early planting, remove crop residues, use pheromone traps'
            },
            'vegetables': {
                'common_pests': ['Aphids', 'Whiteflies', 'Fruit flies', 'Leaf miners'],
                'diseases': ['Bacterial wilt', 'Downy mildew', 'Anthracnose'],
                'control': 'Crop rotation, proper sanitation, integrated pest management'
            }
        }

        if crop and crop.lower() in pests_database:
            return pests_database[crop.lower()]
        else:
            return pests_database


# ==================== TESTING ====================
if __name__ == "__main__":
    ph_api = PhilippineAgriculturalAPIs()

    print("=== PAGASA WEATHER ===")
    weather = ph_api.get_pagasa_weather_forecast()
    if weather:
        for w in weather[:2]:
            print(f"- {w['title']}")

    print("\n=== CROP CALENDAR (RICE) ===")
    calendar = ph_api.get_philippine_crop_calendar('rice')
    print(json.dumps(calendar, indent=2))

    print("\n=== REGIONAL WEATHER (NCR) ===")
    regional = ph_api.get_regional_weather('NCR')
    if regional:
        print(json.dumps(regional['current'], indent=2))

    print("\n=== COMMON PESTS (RICE) ===")
    pests = ph_api.get_common_philippine_pests('rice')
    print(json.dumps(pests['pests'][0], indent=2))

    print("\n=== CROP PRICES ===")
    prices = ph_api.get_market_prices_manual()
    print(json.dumps(prices['prices']['rice'], indent=2))