import dag
from dag import this

@dag.mod("date", default_cmd = this.createdate)
class Date(dag.DagMod):

	@dag.cmd()
	def createdate(self, text = ""):
		return dag.DTime(text)


	@dag.arg("datestr", nargs = -1, nargs_join = " ")
	@dag.cmd( value = this.parse.date(dag.arg("datestr")).formatted )
	def parse(self, datestr = "today"):
		return


	@dag.arg("datestr", nargs = -1, nargs_join = " ")
	@dag.cmd( value = dag.nab.DTime.parse.time(dag.arg("datestr")).formatted )
	def parsetime(self, datestr = "today"):
		return

		
	@dag.cmd( value = dag.nab.DTime.now.utc() )
	def utc(self):
		"""Get current time in UTC"""
		return
		
	@dag.cmd( value = dag.nab.DTime.now.timestamp() )
	def timestamp(self):
		"""Get unix timestamp"""
		return


	@dag.arg.Date('date')
	def daysago(self, date):
		return date.daysago


	@dag.arg.Date('date')
	def yearsago(self, date):
		return date.yearsago