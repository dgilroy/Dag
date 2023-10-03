import dag
from dag.apps.img import img


wikipedia = dag.app.JSON("wikipedia", baseurl = "https://en.wikipedia.org/w/rest.php/v1/")


@wikipedia.hook.pre_http_get
def set_user_agent(request):
	request.headers["User-Agent"] = "fajoifjaf@gmail.com"


@wikipedia.arg.Word("word")
@wikipedia.DEFAULT.collection(value = dag.nab.get("search/page?q={word}&limit=1").pages).CACHE
def search(word = ""):
	"""A simple page query for wikipedia"""
	return


@search.display.MESSAGE("<c b u>Wiki Info: {word}</c b u>")
def display_search(response, formatter):
	for page in response:
		formatter.add_row(page.description)
		
		if page.thumbnail:
			formatter = dag.img.from_url("https:" + page.thumbnail.url).to_formatter(formatter, maxheight = 36)
		else:
			formatter.add_row()


		formatter.add_row(dag.HTML.parse(page.excerpt).printable, style = "bold")