import dag
from dag import this


@dag.mod("cath", baseurl = "http://calapi.inadiutorium.cz/api/v0/en/calendars/general-en/", default_cmd = this.holiday, doc = "http://calapi.inadiutorium.cz/api-doc", dateformat = "%Y/%m/%d",
	spec = "http://calapi.inadiutorium.cz/swagger.yml", response_parser = dag.JSON)
class CatholicCalendar(dag.DagMod):
	"""View Catholic holidays for given day"""
	def _init(self):
		self.color = dag.get_dagcmd("color")


	@dag.arg.Date("day")
	@dag.cmd(cache = True, value = dag.nab.get("{day}"), display = this._display_calendar, message = "Date: {day}")
	def holiday(self, day = "today"):
		"""The holiday for a given day"""
		return


	def _display_calendar(self, response, formatter):		
		for celebration in response.celebrations:
			formatter.add_row(celebration.title, style = "bold " + "".join((self.color.colors(celebration.colour)[:1]) or ""))