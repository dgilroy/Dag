import dag
from dag import r_, resources



basketball = dag.app("basketball", baseurl = "https://api-basketball.p.rapidapi.com/", dateformat="%Y-%m-%d")

@basketball.hook.pre_http_call
def bball_post_params(request):
	request.headers['X-RapidAPI-Host'] = 'api-basketball.p.rapidapi.com'
	request.headers['X-RapidAPI-Key'] = dag.getenv.RAPIDAPIKEY

leagues = basketball.collection("leagues").GET("leagues", r_.response)
leagues.resources("league").label("name").id("id")

# nba = leagues.ops.template(default = 12) # 12 is NBA
# teams = nba.cmd("teams").GET("teams", params = {"league": dag.args.league.id})

teams = leagues.op("teams", default = "nba").GET("teams", params = {"league": dag.args.league.id})


"""
teams.ops(callback = teams).add_ops(
	playerstats = GET("playerstats/{team:id}"),
)
"""


@leagues.op.collection
def teams(league = "nba"):
	year = dag.now().year
	return dag.get("teams", params = {"league": league.id, "season": f"{year-1}-{year}"}).response
teams.resources("team").LABEL("name").ID("id")


@basketball.DEFAULT.collection(cache = resources.status.short == "FT").GET("games", r_.response, params = {"date": dag.args.date})
def games(date: dag.DTime = dag.nab.now()):
	return


@games.display
def display_games(response, formatter, *, league: dag.Resource[leagues] = None):
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

			wteam = hometeam if homescore.total >= awayscore.total else awayteam
			lteam = awayteam if wteam is hometeam else hometeam

			wscore = homescore if wteam is hometeam else awayscore
			lscore = awayscore if wteam is hometeam else homescore

			formatter.add_row(wteam.name, wscore.total, lteam.name, lscore.total)

		formatter.add_row("\n")












"""
leages.op("teams").ARGS( league = dag.arg(int))
"""

"""
leagues.add_ops(
	teams = leagues.op(default = "nba").GET("teams", params = {"league": "{league:id}"}) #12 is NBA
)
"""




"""
from dag.pipes import OP, GET, SUBOP, NO_CACHE

nba = leagues | SUBOP(12)
nbateams = leagues | OP("teams", default = "nba") | NO_CACHE | GET("teams", params = {"league": "{league:id}"}) #12 is NBA
"""