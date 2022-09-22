import dag
from dag import this



@dag.mod("sun", baseurl = "https://api.sunrise-sunset.org/json?", default_cmd = this.time, dateformat = "%Y-%m-%d", doc = 'https://sunrise-sunset.org/api', response_parser = dag.JSON)
class SunriseSunset(dag.DagMod):		
	
	#@dag.hook.pre_http_call
	def unverify_request(self, request):
		request.verify = False

		
	@dag.arg.Date("day")
	@dag.cmd(value = dag.nab.get("lat={lat}&lng={lng}&date={day}").results, cache = True, display = this._display_time, message = "Date: {day}")
	def time(self, day = "today", lat = "35.7796", lng = "-78.6382", *args):
		return
		
		
	def _display_time(self, response, formatter):
		formatter.col(1, "bold")

		for timename, time in response.items():
			date = dag.DTime(time, utc = True).from_utc()
			
			color = ""
			if timename == "sunrise":
				color = "#FF0"
			elif timename == "sunset":
				color = "#0BF"
				
			formatter.add_row(timename.title().replace("_", " "), date.format("%I:%M:%S %p"), style = color)