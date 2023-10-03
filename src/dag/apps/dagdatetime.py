import dag

date = dag.app("date")


@date.DEFAULT.cmd
def createdate(text = ""):
	return dag.DTime(text)


@date.arg.GreedyWords("datestr")
@date.cmd( value = dag.nab.DTime.parse.date(dag.args.datestr).formatted )
def parse(datestr = "today"):
	return


@date.arg.GreedyWords("datestr")
@date.cmd( value = dag.nab.DTime.parse.time(dag.args.datestr).formatted )
def parsetime(datestr = "today"):
	return

	
@date.cmd( value = dag.nab.now().utc )
def utc():
	"""Get current time in UTC"""
	return

	
@date.cmd( value = dag.nab.now().timestamp )
def timestamp():
	"""Get unix timestamp"""
	return


@date.cmd( value = dag.args.date.daysago )
def daysago(date: dag.DTime):
	return


@date.cmd( value = dag.args.date.yearsago )
def yearsago(date: dag.DTime):
	return

now = dag.cmd("now", value = dag.nab.now())