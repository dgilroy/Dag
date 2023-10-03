import dag
from dag import r_


sun = dag.app.JSON("sun", baseurl = "https://api.sunrise-sunset.org/json?", dateformat = "%Y-%m-%d", doc = 'https://sunrise-sunset.org/api', color = "#FDB813")


@sun.DEFAULT.cmd.GET("lat={lat}&lng={lng}&date={day}", r_.results).CACHE
def time(day: dag.DTime = dag.nab.now(), lat = "35.7796", lng = "-78.6382"):
	return


@time.display.MESSAGE("Date: {day}")
def display_time(response, formatter):
	formatter.col(1, "b")

	response = {k:v for k,v in sorted(response.items(), key = lambda item: dag.DTime(item[1]).force_from_utc.make_today)}

	daylength = response.pop("day_length")
	formatter.add_row("Day Length", daylength, style = "u", margin_bottom = 2)

	for timename, time in response.items():
		with formatter.item(time):
			date = dag.DTime(time, utc = True).from_utc
			
			color = ""
			if timename == "sunrise":
				color = "darkorange3"
			elif timename == "sunset":
				color = "#5FF b"
				
			formatter.add_row(timename.title().replace("_", " "), date.format("%I:%M:%S %p"), style = color)