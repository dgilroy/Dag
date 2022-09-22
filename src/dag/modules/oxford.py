import dag
from dag import this




@dag.mod("oxford", baseurl = "https://od-api.oxforddictionaries.com:443/api/v2/", default_cmd = this.define, doc = "https://developer.oxforddictionaries.com/", response_parser = dag.JSON)
class Oxford(dag.DagMod):

	@dag.hook.http_call_headers
	def oxf_call_headers(self, headers):
		headers["app_id"] = "81fc42d7"
		headers["app_key"] = "929d8062f0a32eb0587ec3029e924f88"
		return headers
		
	@dag.arg('word', type = str.lower)
	@dag.cmd(value = dag.nab.get("entries/en-gb/{word}").results, cache = True, message = "Definition: <c bold>{word}</c>", display = this._display_define)
	def define(self, word):
		return
		
	def _display_define(self, response, formatter):
		def_str = ""
		
		for item in response:
			for le in item.lexicalEntries:
				for entry in le.entries:
					formatter.add_row("Etymology" , style = "bold")
					
					for etym in entry.get("etymologies", []):
						formatter.add_row(etym, style = "bold", margin_bottom = 2)

					for sense in entry.senses:
						for definition in sense.get("definitions", []):
							formatter.add_row(definition)
						for example in sense.get("examples", []):
							formatter.add_row(f"    <c bold>Ex:</c> {example.text}")
						
						for subsense in sense.get("subsenses", []):
							for subdef in subsense.definitions:
								formatter.add_row("•" + subdef)