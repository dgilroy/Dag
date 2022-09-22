import shutil
import dag
from dag import this



@dag.mod("wiki", baseurl = "https://en.wikipedia.org/w/rest.php/v1/", default_cmd = this.search, response_parser = dag.JSON)
class Wikipedia(dag.DagMod):

	@dag.hook.pre_http_get
	def set_user_agent(self, request):
		request.headers["User-Agent"] = "fajoifjaf.gmail.com"


	@dag.arg.Word("word")
	@dag.collection(value = dag.nab.get("search/page?q={word}&limit=1").pages, display = this._display_search, message = dag.nab("<c b u>Wiki Info: {word}</c b u>"), cache = True)
	def search(self, word = ""):
		"""A simple page query for wiki"""
		return


	def _display_search(self, response, formatter):
		for page in response:
			img = dag.get_dagcmd("img")

			formatter.add_row(page.description)
			
			if page.thumbnail:
				formatter = dag.img.from_url("https:" + page.thumbnail.url).to_formatter(formatter, maxheight = 36)
			else:
				formatter.add_row()


			formatter.add_row(dag.HTML(page.excerpt).text, style = "bold")