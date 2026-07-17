from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from datetime import datetime
import time

app = Flask(__name__)
CORS(app)

@app.route('/weather', methods=['GET'])
def get_weather():
    city = request.args.get('city', '').strip()
    state = request.args.get('state', '').strip()
    
    if not city:
        return jsonify({"error": "Please enter a city name"}), 400
    
    try:
        # Always search with just city name + India for better results
        search_query = f"{city}, India"
        
        # Nominatim headers - THIS IS CRITICAL
        headers = {
            "User-Agent": "WeatherApp/1.0 (contact@weatherapp.com)",
            "Accept": "application/json"
        }
        
        params = {
            "q": search_query,
            "format": "json",
            "limit": 10,  # Get more results to find the best match
            "addressdetails": 1
        }
        
        print(f"🔍 Searching: {search_query}")
        if state:
            print(f"   Looking for state/district: {state}")
        
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params=params,
            headers=headers
        )
        
        print(f"📡 Status: {response.status_code}")
        
        if response.status_code != 200:
            return jsonify({"error": "Location service unavailable"}), 500
            
        results = response.json()
        print(f"📦 Found: {len(results)} results")
        
        if not results:
            return jsonify({
                "error": f"Location '{city}' not found. Try adding the state."
            }), 404
        
        # Debug: print all results with detailed info
        for i, r in enumerate(results):
            addr = r.get("address", {})
            relevance = r.get("importance", 0)
            # Print all address hierarchy fields
            print(f"  [{i}] Name: {r.get('name')} | Type: {r.get('type', 'N/A')}")
            print(f"       Address keys: {list(addr.keys())}")
            print(f"       State: {addr.get('state', 'N/A')} | District: {addr.get('district', 'N/A')} | City: {addr.get('city', 'N/A')} | Town: {addr.get('town', 'N/A')} | Village: {addr.get('village', 'N/A')}")
        
        # Smart matching algorithm - more flexible
        result = None
        best_score = -1
        
        if state:
            state_lower = state.lower()
            
            # Score each result based on how well it matches
            for r in results:
                addr = r.get("address", {})
                r_name = r.get("name", "").lower()
                
                # Extract all possible location fields
                r_state = addr.get("state", "").lower()
                r_district = addr.get("district", "").lower()
                r_city = addr.get("city", "").lower()
                r_town = addr.get("town", "").lower()
                r_village = addr.get("village", "").lower()
                
                score = 0
                match_location = ""
                
                # Check if state/district matches
                state_match = False
                if r_state == state_lower:
                    state_match = True
                    match_location = r_state
                    score += 100
                    print(f"    State match: {r_state}")
                elif r_district == state_lower:
                    state_match = True
                    match_location = r_district
                    score += 100
                    print(f"    District match: {r_district}")
                
                # Check if location name matches
                city_lower = city.lower()
                if r_name == city_lower:
                    if state_match:
                        score += 50  # Exact name match with state
                    else:
                        score += 20  # Exact name but wrong state (still useful)
                elif r_city == city_lower or r_town == city_lower or r_village == city_lower:
                    if state_match:
                        score += 40
                    else:
                        score += 15
                
                print(f"  [{r.get('name')}] Score: {score} | State Match: {state_match}")
                
                if score > best_score:
                    best_score = score
                    result = r
                    if state_match:
                        print(f"    ✅ New best match (STATE MATCHED)!")
                    else:
                        print(f"    ✅ New best match")
            
            # If we found a state match, use it. Otherwise try without state constraint
            if not result or best_score < 50:  # Threshold for acceptable match
                print(f"\n⚠️  State '{state}' not found in results. Trying without state constraint...")
                result = None
                best_score = -1
                
                # Re-score without state requirement
                for r in results:
                    r_name = r.get("name", "").lower()
                    city_lower = city.lower()
                    
                    score = 0
                    if r_name == city_lower:
                        score = 100  # Exact match
                    elif city_lower in r_name or r_name in city_lower:
                        score = 50  # Partial match
                    
                    if score > best_score:
                        best_score = score
                        result = r
                
                if result:
                    print(f"✅ Using best match by name: {result.get('name')}")
        
        # Final fallback: Use first result (highest relevance)
        if not result:
            result = results[0]
            addr = result.get("address", {})
            match_info = addr.get("state", addr.get("district", "Unknown"))
            print(f"✅ Using top result: {result.get('name')} in {match_info}")
        
        lat = float(result["lat"])
        lon = float(result["lon"])
        address = result.get("address", {})
        name = result.get("name", city)
        
        # Extract state/region info from multiple possible fields
        state_name = address.get("state", "") or address.get("district", "")
        if not state_name:
            state_name = address.get("county", "")
        
        country = address.get("country", "India")
        
        print(f"✅ Final: {name}, {state_name}\n")
        
        # Get weather
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": True,
            "timezone": "auto"
        }
        
        weather_res = requests.get(weather_url, params=weather_params).json()
        
        if "current_weather" not in weather_res:
            return jsonify({"error": "Weather data not available"}), 404

        current = weather_res["current_weather"]
        
        # Weather codes
        weather_codes = {
            0: "Clear Sky", 1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast",
            45: "Foggy", 48: "Foggy",
            51: "Light Drizzle", 53: "Moderate Drizzle", 55: "Dense Drizzle",
            61: "Slight Rain", 63: "Moderate Rain", 65: "Heavy Rain",
            71: "Slight Snow", 73: "Moderate Snow", 75: "Heavy Snow",
            80: "Rain Showers", 81: "Rain Showers", 82: "Rain Showers",
            95: "Thunderstorm", 96: "Thunderstorm", 99: "Thunderstorm"
        }
        code = current.get("weathercode", 0)
        description = weather_codes.get(code, "Unknown")
        
        icons = {
            0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️",
            45: "🌫️", 48: "🌫️",
            51: "🌧️", 53: "🌧️", 55: "🌧️",
            61: "🌧️", 63: "🌧️", 65: "⛈️",
            71: "❄️", 73: "❄️", 75: "❄️",
            80: "🌧️", 81: "🌧️", 82: "⛈️",
            95: "⛈️", 96: "⛈️", 99: "⛈️"
        }
        icon = icons.get(code, "🌤️")
        
        wind_dir = current.get("winddirection", 0)
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        idx = round(wind_dir / 45) % 8
        dir_text = directions[idx]

        region = f"{state_name}, {country}" if state_name else country

        return jsonify({
            "city": name,
            "region": region,
            "temperature": round(current["temperature"]),
            "icon": icon,
            "description": description,
            "wind": f"{current['windspeed']} km/h",
            "direction": f"{dir_text} ({wind_dir}°)",
            "time": current["time"]
        })

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "time": datetime.now().isoformat()})

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Weather API is running!"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)