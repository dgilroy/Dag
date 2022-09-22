import dag
from dag import this	


@dag.mod("weather", baseurl = "https://api.weather.gov/", default_cmd = this.forecast, doc = "https://www.weather.gov/documentation/services-web-api",
			spec = "https://api.weather.gov/openapi.json", response_parser = dag.JSON)
class Weather(dag.DagMod):

	@dag.cmd(value = dag.nab.get("gridpoints/RAH/73,57/forecast").properties.periods, display = this._display_forecast)
	def forecast(self):
		"""Get the weather forecast for RDU"""
		return

		
	def _display_forecast(self, response, formatter):
		formatter.col(1, after = "˚F")
		
		for idx, period in enumerate(reversed(response)):
			is_day = period.name.lower().find("night") < 0
			formatter.col(1, "#F00" if is_day else "#4FF")
				
			formatter.add_row(period.name, period.temperature, period.detailedForecast, style = "bold" if idx+1 == len(response) else "", margin_bottom = 1 if not is_day else 2)
		
		
	@dag.resources(label = "{properties.name}")
	@dag.collection(value = dag.nab.get("radar/stations").features)
	def radars(self):
		pass