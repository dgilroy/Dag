import dag


sptrans = dag.app.JSON("sp", baseurl = "https://dictionaryapi.com/api/v3/references/spanish/json/", auth = dag.auth.PARAM("key", 
	dag.nab.env.MERIAM_WEBSTER_TRANSLATOR_APIKEY))


@dag.arg.Word("word")
@sptrans.DEFAULT.cmd.CACHE.GET("{word}")
def translate(word):
	return


@translate.display.MESSAGE("Word: {word}")
def _display(response, formatter, parsed):
	for info in response:
		with dag.passexc():
			if not parsed.word in info.meta.id:
				continue
			formatter.add_row(f"<c  u b>{info.meta.id.split(':')[0]}</c u b>({info.fl})", info.shortdef[0])