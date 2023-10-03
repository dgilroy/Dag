import dag


hebcal = dag.app.JSON("hebrew", baseurl = "http://www.hebcal.com/converter/", doc = "https://www.hebcal.com/home/developer-apis", dateformat = "gy=%Y&gm=%m&gd=%d")

calendar = hebcal.DEFAULT.cmd("calendar").CACHE.GET("?cfg=json&g2h=1&{day}")
calendar.add_dagarg.Date("day", default = dag.nab.now())


@calendar.display.MESSAGE("Date: {day}")
def _display_calendar(response, formatter):
	formatter.col(0, "bold", margin = 1)
	
	formatter.add_row("Hebrew Year:", response.hy)
	formatter.add_row("Hebrew Month:", response.hm)
	formatter.add_row("Hebrew Day:", response.hd)

	for i, event in enumerate(response.events):
		formatter.add_row("Events:" if i == 0 else "", event)