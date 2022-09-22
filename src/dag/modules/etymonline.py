import dag
from dag import this


@dag.mod("etym", baseurl = "https://www.etymonline.com/search?q=", response_parser = dag.HTML, default_cmd = this.etym)
class Etymonline(dag.DagMod):
	"""Search for a word's etymology"""
	
	@dag.arg.Word("word", nargs = -1)
	@dag.resources(launch = "https://www.etymonline.com/word/{word}")
	@dag.collection(value = dag.nab.get(dag.arg("word")).css("[class ^= word--]"), message = "<c bold>Search: {word}</c>", display = this._display_etym, idx = True, cache = True)
	def etym(self, word = ""):
		"""Search for a word's etymology"""
		return
		
		
	def _display_etym(self, response, formatter, parsed):
		formatter.col(0, "bold", margin = 2).col(1, max_width = 72)

		for word in reversed(response):
			breakpoint()
			formatter.add_row(word.select('a[class ^= word__name--]')[0].text, word.select('[class ^= word__defination--]')[0].text, margin_bottom = 2)
		
		formatter.cstyle(parsed.word, "b u", ignorecase = True)