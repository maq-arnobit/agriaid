import requests
import json
from datetime import datetime
from api_services import AgriculturalAPIs
from philippine_apis import PhilippineAgriculturalAPIs
import os
from dotenv import load_dotenv

load_dotenv()

class FarmerChatbot:
    def __init__(self):
        self.ollama_url = os.getenv('OLLAMA_HOST', 'http://localhost:11434') + '/api/generate'
        self.model = os.getenv('OLLAMA_MODEL', 'agriaid')
        self.conversation_history = []

        # Initialize API services
        self.global_apis = AgriculturalAPIs()
        self.ph_apis = PhilippineAgriculturalAPIs()

    def detect_intent(self, user_input):
        """Detect what the user is asking about"""
        user_input_lower = user_input.lower()

        intents = {
            'weather': ['weather', 'temperature', 'temp', 'rain', 'ulan', 'forecast', 'climate', 'bagyo', 'typhoon',
                        'init', 'lamig'],
            'soil': ['soil', 'lupa', 'moisture', 'ph', 'fertility', 'nutrients', 'pataba'],
            'pest': ['pest', 'insect', 'kulisap', 'bug', 'disease', 'sakit', 'damage', 'infestation', 'peste'],
            'crop': ['crop', 'plant', 'tanim', 'grow', 'harvest', 'ani', 'yield', 'palay', 'mais', 'gulay'],
            'news': ['news', 'balita', 'article', 'latest', 'update', 'information', 'advisory'],
            'price': ['price', 'presyo', 'market', 'sell', 'cost', 'value', 'halaga']
        }

        detected = []
        for intent, keywords in intents.items():
            if any(keyword in user_input_lower for keyword in keywords):
                detected.append(intent)

        return detected if detected else ['general']

    def gather_context_data(self, intents, location, lat=None, lon=None, region=None):
        """Gather both global and Philippine-specific data"""
        context = {}

        # Default coordinates for Manila if not provided
        if not lat or not lon:
            lat, lon = 14.5995, 120.9842

        # Philippine-specific data (prioritized)
        if 'weather' in intents:
            print("📡 Fetching PAGASA and weather data...")

            # PAGASA forecast
            pagasa = self.ph_apis.get_pagasa_weather_forecast()
            context['pagasa_weather'] = pagasa

            # Regional weather
            if region:
                regional = self.ph_apis.get_regional_weather(region)
                context['regional_weather'] = regional

            # Typhoon alerts
            typhoon = self.ph_apis.get_pagasa_tropical_cyclone_info()
            context['typhoon_alert'] = typhoon

            # Detailed weather from Open-Meteo
            detailed = self.global_apis.get_open_meteo_weather(lat, lon)
            context['detailed_weather'] = detailed

        if 'soil' in intents:
            print("📡 Fetching soil data...")
            soil = self.global_apis.get_soil_data(lat, lon)
            context['soil'] = soil

        if 'pest' in intents:
            print("📡 Loading pest information...")
            ph_pests = self.ph_apis.get_common_philippine_pests()
            context['ph_pests'] = ph_pests

            observations = self.global_apis.get_pest_observations(lat, lon)
            context['pest_observations'] = observations

        if 'crop' in intents:
            print("📡 Loading crop calendar...")
            # Try to detect crop type
            crops = ['rice', 'corn', 'vegetables', 'banana']
            for crop in crops:
                if crop in intents or crop in str(self.conversation_history[-1:]).lower():
                    calendar = self.ph_apis.get_philippine_crop_calendar(crop)
                    context['crop_calendar'] = calendar
                    break

        if 'price' in intents:
            print("📡 Fetching market prices...")
            prices = self.ph_apis.get_market_prices_manual()
            context['prices'] = prices

        if 'news' in intents:
            print("📡 Fetching agricultural news...")
            da_advisories = self.ph_apis.get_da_advisories()
            context['da_advisories'] = da_advisories

            news = self.global_apis.get_agricultural_news(query="philippines agriculture")
            context['news'] = news

        return context

    def format_context_for_llm(self, context):
        """Format gathered data for LLM consumption"""
        formatted = "\n\n[REAL-TIME AGRICULTURAL DATA]\n"

        # PAGASA Weather
        if 'pagasa_weather' in context and context['pagasa_weather']:
            formatted += f"\n🇵🇭 PAGASA WEATHER FORECAST:\n"
            for forecast in context['pagasa_weather'][:3]:
                formatted += f"- {forecast['title']}\n"
                formatted += f"  {forecast['summary'][:200]}...\n"

        # Typhoon alerts
        if 'typhoon_alert' in context and context['typhoon_alert']:
            if isinstance(context['typhoon_alert'], str):
                formatted += f"\n⚠️ TYPHOON STATUS: {context['typhoon_alert']}\n"
            else:
                formatted += f"\n⚠️ TYPHOON ALERT:\n"
                for alert in context['typhoon_alert'][:2]:
                    formatted += f"  {alert['content'][:200]}...\n"

        # Detailed weather
        if 'detailed_weather' in context and context['detailed_weather']:
            if 'current' in context['detailed_weather']:
                w = context['detailed_weather']['current']
                formatted += f"\n🌤️ DETAILED CONDITIONS:\n"
                formatted += f"- Temperature: {w.get('temperature', 'N/A')}°C\n"
                formatted += f"- Humidity: {w.get('humidity', 'N/A')}%\n"
                formatted += f"- Wind: {w.get('windspeed', 'N/A')} km/h\n"
                formatted += f"- Precipitation: {w.get('precipitation', 0)} mm\n"

        # Soil data
        if 'soil' in context and context['soil']:
            s = context['soil']
            formatted += f"\n🌱 SOIL CONDITIONS:\n"
            formatted += f"- Temperature: {s['soil_temp']}°C\n"
            formatted += f"- Moisture: {s['soil_moisture']}\n"

        # Pest info
        if 'ph_pests' in context and context['ph_pests']:
            formatted += f"\n🐛 COMMON PHILIPPINE PESTS:\n"
            if 'pests' in context['ph_pests']:
                for pest in context['ph_pests']['pests'][:2]:
                    formatted += f"- {pest['name']}: {pest['symptoms']}\n"

        # Prices
        if 'prices' in context and context['prices']:
            formatted += f"\n💰 CURRENT MARKET PRICES (as of {context['prices']['last_updated']}):\n"
            if 'rice' in context['prices']['prices']:
                formatted += f"- Rice: {context['prices']['prices']['rice']['regular_milled']}\n"

        # News and advisories
        if 'da_advisories' in context and context['da_advisories']:
            formatted += f"\n📰 DA ADVISORIES:\n"
            for advisory in context['da_advisories'][:3]:
                formatted += f"- {advisory['title']}\n  {advisory['link']}\n"

        if 'news' in context and context['news']:
            formatted += f"\n📡 LATEST AGRICULTURAL NEWS:\n"
            for article in context['news'][:3]:
                formatted += f"- {article['title']}\n  {article['url']}\n"

        formatted += "\n[END OF REAL-TIME DATA]\n"

        return formatted

    def chat(self, user_input, location="Manila", lat=None, lon=None, region=None, stream=False):
        """Main chat function"""
        # Detect intents
        intents = self.detect_intent(user_input)
        print(f"🤖 Detected: {', '.join(intents)}")

        # Gather context data
        context_data = self.gather_context_data(intents, location, lat, lon, region)

        # Format context
        context_text = self.format_context_for_llm(context_data)

        # Enhance prompt
        enhanced_prompt = user_input + context_text

        # Add to history
        self.conversation_history.append({
            "role": "user",
            "content": enhanced_prompt
        })

        # Build conversation
        full_prompt = ""
        for msg in self.conversation_history[-10:]:
            full_prompt += f"{msg['role']}: {msg['content']}\n"

        # Call Ollama
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": stream
        }

        try:
            if stream:
                return self._stream_response(payload)
            else:
                # response = requests.post(self.ollama_url, json=payload)
                # result = response.json()
                # assistant_response = result['response']
                #
                # self.conversation_history.append({
                #     "role": "assistant",
                #     "content": assistant_response
                # })
                #
                # return assistant_response
                response = requests.post(self.ollama_url, json=payload, timeout=60)
                print(f"📡 Response status: {response.status_code}")

                if response.status_code != 200:
                    error_msg = f"Ollama error: {response.status_code} - {response.text}"
                    print(error_msg)
                    return error_msg

                result = response.json()
                print(f"🔍 Response keys: {list(result.keys())}")

                # Try to get response
                try:
                    assistant_response = result['response']  # This line might be failing
                    print(f"✅ Got response: {assistant_response[:100]}...")
                except KeyError as e:
                    print(f"❌ KeyError: {e}")
                    print(f"🔍 Full result keys: {result.keys()}")
                    print(f"🔍 Full result: {json.dumps(result, indent=2)[:500]}")
                    return f"Error: 'response' key not found in Ollama output"

                # Check if response is empty
                if not assistant_response or not assistant_response.strip():
                    print("⚠️ Empty response from Ollama")
                    return "I apologize, I couldn't generate a response. Please try again."

                self.conversation_history.append({
                    "role": "assistant",
                    "content": assistant_response
                })
                return assistant_response
        except Exception as e:
            return f"❌ Error: {e}"

    def _stream_response(self, payload):
        """Stream responses in real-time"""
        try:
            response = requests.post(self.ollama_url, json=payload, stream=True, timeout=60)

            if response.status_code != 200:
                error_msg = f"Ollama error: {response.status_code}"
                print(f"\n🤖 Bot: {error_msg}")
                return error_msg

            full_response = ""
            print("\n🤖 Bot: ", end='', flush=True)

            for line in response.iter_lines():
                if line:
                    try:
                        json_response = json.loads(line)

                        if 'response' in json_response:
                            token = json_response['response']
                            full_response += token
                            print(token, end='', flush=True)

                        # Check if generation is done
                        if json_response.get('done', False):
                            break

                    except json.JSONDecodeError:
                        continue

            print()  # New line after streaming

            # Check if we got any response
            if not full_response or not full_response.strip():
                fallback = "I apologize, I couldn't generate a response. Please try again."
                print(f"⚠️ Empty response, using fallback")
                full_response = fallback

            self.conversation_history.append({
                "role": "assistant",
                "content": full_response
            })

            return full_response

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"\n🤖 Bot: {error_msg}")
            return error_msg

    def reset_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []
        print("✅ Conversation reset")


# ==================== CLI Interface ====================
if __name__ == "__main__":
    print("=" * 70)
    print("🌾 PHILIPPINE FARMER ASSISTANT CHATBOT")
    print("=" * 70)
    print("\nKumusta! I'm your agricultural assistant powered by AI.")
    print("\nI can help with:")
    print("  🌤️  PAGASA weather and typhoon alerts")
    print("  🌾  Crop planting schedules (palay, mais, gulay)")
    print("  🐛  Pest identification and control")
    print("  💰  Market prices")
    print("  📰  DA advisories and agricultural news")
    print("  🌱  Soil and farming tips")
    print("\nCommands:")
    print("  'reset' - Clear conversation")
    print("  'quit' or 'exit' - Exit chatbot")
    print("\n" + "=" * 70)

    bot = FarmerChatbot()

    # Get location
    location = input("\n📍 Enter your city/municipality (default: Manila): ") or "Manila"
    region = input("📍 Enter your region (e.g., NCR, III, IV-A): ") or None

    print(f"\n✅ Location set to: {location}" + (f", Region {region}" if region else ""))
    print("\nType your question below:\n")

    while True:
        try:
            user_input = input(f"\n👨‍🌾 You: ")

            if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                print("\n🤖 Bot: Salamat! Happy farming! 🌾")
                break

            if user_input.lower() == 'reset':
                bot.reset_conversation()
                continue

            if not user_input.strip():
                continue

            # Use streaming for better UX
            try:
                bot.chat(user_input, location=location, region=region, stream=True)
            except KeyboardInterrupt:
                print("\n\n⚠️ Interrupted by user")
                continue
            except Exception as e:
                print(f"\n❌ Error: {e}")
                continue

        except KeyboardInterrupt:
            print("\n\n🤖 Bot: Goodbye! 🌾")
            break
        except EOFError:
            print("\n\n🤖 Bot: Goodbye! 🌾")
            break