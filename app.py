from flask import Flask, request, render_template
import requests
import pycountry
import unicodedata
from dotenv import load_dotenv
import os

app = Flask(__name__)
countries = sorted(pycountry.countries, key=lambda c: c.name)

load_dotenv()
api_key = os.getenv("API_KEY")
base_url = "https://api.openweathermap.org/data/2.5/weather?"

def normalize_text(s):
    normalized = unicodedata.normalize('NFD', s)
    ascii_text = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    return ascii_text

def get_weather(country_code, city_name):
    try:
        # Build URL
        complete_url = f"{base_url}q={city_name},{country_code}&units=metric&appid={api_key}"
        response = requests.get(complete_url, timeout=5)
        data = response.json()
    except requests.exceptions.RequestException:
        # Network / connection / timeout problems
        return {"error": "Could not reach the weather service. Check your internet connection."}

    cod = data.get("cod")

    # Success
    if cod == 200:
        main = data["main"]
        weather = data["weather"][0]
        condition_main = weather["main"].lower()  # e.g. "Clear" -> "clear"

        if condition_main == "clear":
            theme = "sunny-bg"
        elif condition_main in ("rain", "drizzle"):
            theme = "rainy-bg"
        elif condition_main == "snow":
            theme = "snowy-bg"
        elif condition_main == "clouds":
            theme = "cloudy-bg"
        elif condition_main == "thunderstorm":
            theme = "stormy-bg"
        else:
            theme = "default-bg"

        # Look up full country name for display
        country = pycountry.countries.get(alpha_2=country_code.upper())
        country_name = country.name if country else country_code

        return {
            "city": city_name,
            "country": country_name,
            "temp": main["temp"],
            "pressure": main["pressure"],
            "humidity": main["humidity"],
            "description": weather["description"].title(),
            "icon": weather["icon"],
            "theme": theme,  #
        }

    # City not found (common case)
    if cod == "404" or cod == 404:
        return {"error": f"Could not find the city “{city_name}” in that country. Check the spelling."}

    # Invalid API key
    if cod == 401:
        return {"error": "There is a problem with the API key. (This is on the developer side.)"}

    # Fallback for anything else
    return {"error": data.get("message", "Something went wrong while getting the weather.")}

@app.route("/", methods=["GET", "POST"])
def home():
    weather_data = None
    error_message = None

    if request.method == "POST":
        country_code = request.form.get("country", "").strip()
        city_raw = request.form.get("city", "").strip()
        city_name = normalize_text(city_raw)

        if not country_code or not city_name:
            error_message = "Please select a country and enter a city name."
        else:
            result = get_weather(country_code, city_name)
            if "error" in result:
                error_message = result["error"]
            else:
                weather_data = result


    return render_template(
        "index.html",
        weather=weather_data,
        error=error_message,
        countries=countries,
    )


if __name__ == "__main__":
    app.run(debug=True)
