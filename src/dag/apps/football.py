import dag
from dag import r_, resources


def nfl_preformatter(formatter):
	formatter.cstyle(r"Carolina Panthers", "#0085CA", prefix = "🐱", rowstyle="bg-#19")
	formatter.cstyle(r"North Carolina$", "#7BAFD4", prefix = "🦶", rowstyle="bg-#19")
	formatter.cstyle(r"Appalachian State", "#FFCC00", prefix = "⛰️")
	formatter.cstyle(r"NC State", "#FF0000", prefix = "🐺")
	formatter.cstyle(r"Duke", "#00539B", prefix = "😈")



nfl = dag.app("nfl", baseurl = "https://api-american-football.p.rapidapi.com/", dateformat="%Y-%m-%d", preformatter = nfl_preformatter)

@nfl.hook.pre_http_call
def bball_post_params(request):
	request.headers['X-RapidAPI-Host'] = 'api-american-football.p.rapidapi.com'
	request.headers['X-RapidAPI-Key'] = dag.getenv.RAPIDAPIKEY

leagues = nfl.collection("leagues").GET("leagues", r_.response)
leagues.resources("league").label("league.name").id("league.id")


teams = leagues.op("teams", default = "nfl").GET("teams", params = {"league": dag.args.league.id}) #12 is NBA


@leagues.op.collection
def teams(league = "nfl"):
	year = dag.now().year
	return dag.get("teams", params = {"league": league.id, "season": f"{year-1}-{year}"}).response
teams.resources("team").LABEL("name").ID("id")


@nfl.DEFAULT.collection(cache = resources.status.short == "FT").GET("games", r_.response, params = {"date": dag.args.date, "timezone": "America/New_York"})
def games(date: dag.DTime = dag.nab.now().force_from_utc):
	return


@games.display.MESSAGE("Date: {date}")
def display_games(response, formatter, *, league: dag.Resource[leagues] = None):
	if not response:
		return
		
	leaguegames = response.partition("league.name")

	for leaguename, games in leaguegames.items():
		if league and league.name != leaguename:
			continue

		formatter.add_row("League: " + leaguename, style = "b u red")

		for game in games:
			hometeam = game.teams.home
			homescore = game.scores.home

			awayteam = game.teams.away
			awayscore = game.scores.away

			try:
				wteam, wscore = (hometeam, homescore) if homescore.total >= awayscore.total else (awayteam, awayscore)
				lteam, lscore = (awayteam, awayscore) if wteam is hometeam else (hometeam, homescore)

				#wscore = homescore if wteam is hometeam else awayscore

				formatter.add_row(wteam.name, wscore.total, lteam.name, lscore.total)
			except Exception:
				continue

		formatter.add_row("\n")