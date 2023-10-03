import dag
from dag.apps.color import color


cath = dag.app.JSON("cath", baseurl = "http://calapi.inadiutorium.cz/api/v0/en/calendars/general-en/", doc = "http://calapi.inadiutorium.cz/api-doc", dateformat = "%Y/%m/%d",
	spec = "http://calapi.inadiutorium.cz/swagger.yml", help = "View Catholic holidays for given day")


holiday = cath.DEFAULT.cmd.CACHE.GET(dag.args.day)
holiday.add_dagarg.Date("day", default = dag.nab.now())


#holiday.display(r_.title, foreach = r_.celebrations, style = "bold " + (color.nab.colors(r_.colour)[:1] | [""])[0]).MESSAGE("Date: {day}")

@holiday.display.MESSAGE("Date: {day}")
def display_calendar(response, formatter):
	for celebration in response.celebrations:
		formatter.add_row(celebration.title, style = "bold " + ((color.colors(celebration.colour)[:1] or [""])[0]))