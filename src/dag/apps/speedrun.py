import dag
from dag import r_


speedrun = dag.app.JSON("speedrun", baseurl = f"https://www.speedrun.com/api/v1/", doc = "https://github.com/speedruncomorg/api/tree/master/version1")


#@speedrun.collection.DEFAULT.GET("games", r_.data)
#@speedrun.collection.DEFAULT.CACHE.GET("games", r_.data, pager = dag.Pager(offset = r_.pagination.offset, max = 1000))
@speedrun.DEFAULT.collection.CACHE
def games():
	#games = dag.get("games?_bulk=yes&max=1000", pager = dag.Pager(offset = r_.pagination.offset, max = 1000))
	games = dag.get("games?_bulk=yes&max=1000")
	data = games.data

	urls = []

	while games.pagination:
		url = games.pagination.links[-1].uri

		if not url:
			break

		if url in urls:
			break

		urls.append(url)

		games = dag.get(url)
		data.extend(games.data)

	return data
games.resources("game").id("id").label("names.international")