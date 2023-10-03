import dag
from dag import r_


weather = dag.app.JSON("weather", baseurl = "https://api.weather.gov/", doc = "https://www.weather.gov/documentation/services-web-api",
			spec = "https://api.weather.gov/openapi.json")

forecast = weather.DEFAULT.cmd.GET("gridpoints/RAH/73,57/forecast", r_.properties.periods)
forecast.settings.help = "Get the weather of RDU"

@forecast.display
def display_forecast(response, formatter):
	formatter.col(1, after = "˚F")
	
	for idx, period in enumerate(reversed(response)):
		is_day = period.name.lower().find("night") < 0
		formatter.col(1, "#F00" if is_day else "#4FF")
			
		formatter.add_row(period.name, period.temperature, period.detailedForecast, style = "bold" if idx+1 == len(response) else "", margin_bottom = 1 if not is_day else 2)
	
	
radars = weather.collection.GET("radar/stations", r_.features)
radars.resources("radar").label("{properties.name}")