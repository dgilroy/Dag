import dag
from dag import this	


@dag.mod("hebrew", baseurl = "http://www.hebcal.com/converter/", default_cmd = this.calendar, doc = "https://www.hebcal.com/home/developer-apis", dateformat = "gy=%Y&gm=%m&gd=%d", response_parser = dag.JSON)
class HebrewCalendar(dag.DagMod):

	@dag.arg.Date("day")
	@dag.cmd(cache = True, value = dag.nab.get("?cfg=json&g2h=1&{day}"), display = this._display_calendar, message = "Date: {day}")
	def calendar(self, day = "today"):
		return


	def _display_calendar(self, response, formatter):
		formatter.col(0, "bold", margin = 1, after = ":")
		
		
		formatter.add_row("Hebrew Year", response.hy)
		formatter.add_row("Hebrew Month", response.hm)
		formatter.add_row("Hebrew Day", response.hd)