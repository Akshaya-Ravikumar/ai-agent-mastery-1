"""
Exercise 1: Weather Fetcher
=============================
Difficulty: Beginner | Time: 1.5 hours

Task:
Create a function that takes a city name, calls the wttr.in API,
and returns a dictionary with temperature and conditions.
Handle errors gracefully.

Instructions:
1. Complete the fetch_weather() function below
2. Handle edge cases: empty city, API timeout, invalid city
3. Test with at least 3 different cities
4. Bonus: Add wind speed and humidity to the output

Run: python exercise_01_weather_fetcher.py
"""

import requests


def fetch_weather(city: str) -> dict:
    """Fetch weather data for a given city.

    Args:
        city: Name of the city

    Returns:
        Dictionary with keys: city, temperature_c, conditions

    Raises:
        ValueError: If city is empty or API call fails
    """
    # TODO: Implement this function
    # 1. Validate the city input (not empty)
    # 2. Make a GET request to https://wttr.in/{city}?format=j1
    # 3. Parse the JSON response
    # 4. Extract temperature and conditions
    # 5. Handle errors (timeout, invalid city, etc.)

    if not city or not city.strip(): 
        raise ValueError("City is Empty!")
    
    try:
      response = requests.get(f"https://wttr.in/{city}?format=j1", timeout=10)
      response.raise_for_status()

      data = response.json()

      current_condition = data.get('current_condition')

      if not current_condition:
        raise ValueError('Current Condition missing in API response')
      
      current = current_condition[0]
      return {
          "city" : city,
          "temperature_in_celcius": current["temp_C"],
          "temperature_in_farenheit": current["temp_F"],
          "humidity": current["humidity"],
          "weather_description": current.get("weatherDesc")[0].get("value")
      }

    except requests.exceptions.Timeout:
        raise ValueError("Request timed out")
    except Exception as e:
      raise ValueError(f"An unexpected error occurred while fetching weather for '{city}': {e}")


# === Test your implementation ===
if __name__ == "__main__":
    # Test 1: Valid city
    print("Test 1: London")
    result = fetch_weather("London")
    print(result)

    # Test 2: Another valid city
    print("Test 2: Tokyo")
    result = fetch_weather("Tokyo")
    print(result)

    # Test 3: Error handling - empty city
    print("Test 3: Empty city (should raise ValueError)")
    try:
       result = fetch_weather("")
    except ValueError as e:
       print(f"Caught error: {e}")
