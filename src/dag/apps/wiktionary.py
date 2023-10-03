import dag


wiktionary = dag.app.JSON("wiktionary", baseurl = "https://en.wiktionary.org/w/api.php?action=query&format=json&list=search&utf8=1&srsearch=",  doc = "https://en.wiktionary.org/w/api.php")

@wiktionary.DEFAULT.cmd.CACHE.GET(dag.args.word)
def define(word = ""):
	"""The holiday for a given day"""
	return


@define.display.MESSAGE("Define: {word}")
def display_definition(response, formatter):		
	return response
	breakpoint()
	for i, celebration in enumerate(response.celebrations):
		formatter.add_row(celebration.title, style = "bold")