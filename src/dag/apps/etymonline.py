import dag
from dag import r_


etym = dag.app.HTML("etym", baseurl = "https://www.etymonline.com/search?q=", help = "Search for a word's etymology")


lookup = etym.DEFAULT.collection("lookup", help = "Search for a word's etymology").CACHE.GET(dag.args.word, r_.css("[class ^= word--]"))
lookup.add_arg.Word("word")
lookup.resources.launch("https://www.etymonline.com/word/{word}")
	

@lookup.display.MESSAGE("<c bold>Search: {word}</c>")
def display_etym(response, formatter, parsed):
	formatter.col(0, "bold", margin = 2).col(1, max_width = 72)

	for word in formatter.idxitems(reversed(response)):
		formatter.add_row(word.select('a[class ^= word__name--]')[0].printable, word.select('[class ^= word__defination--]')[0].printable, margin_bottom = 2)
	
	formatter.icstyle(parsed.word, "b u #F88")