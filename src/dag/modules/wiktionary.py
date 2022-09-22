import dag
from dag import this



@dag.mod("wiktionary", baseurl = "https://en.wiktionary.org/w/api.php?action=query&format=json&list=search&utf8=1&srsearch=", default_cmd = this.define,
			doc = "https://en.wiktionary.org/w/api.php", response_parser = dag.JSON)
class CatholicCalendar(dag.DagMod):
	"""View Catholic holidays for given day"""

	@dag.arg("word")
	@dag.cmd(cache = True, value = dag.nab.get("{word}"), display = this._display_definition, message = "Define: {word}")
	def define(self, word = ""):
		"""The holiday for a given day"""
		return

	def _display_definition(self, response, formatter):		
		return response
		breakpoint()
		for i, celebration in enumerate(response.celebrations):
			formatter.add_row(celebration.title, style = "bold")