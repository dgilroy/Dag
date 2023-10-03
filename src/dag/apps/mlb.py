import dag
from dag import resources


mlb = dag.app.JSON("mlb", baseurl = "https://statsapi.mlb.com/api/v1/", help = "Gets MLB Scores", dateformat = "%Y-%m-%d")

@mlb.DEFAULT.collection(value = dag.nab.get("schedule?sportId=1&hydrate=linescore(runners)&date={day}").dates[0].games, catch = (IndexError, AttributeError), cache = resources.status.abstractGameCode == "F")
def games(day: dag.DTime = dag.nab.now()):
	"""See MLB game scores for a given date"""
	return

@games.display.MESSAGE("Date: {day}")
def _display_games(response, formatter):
	formatter.col(style = "bold", margin = 3, just = str.rjust)
	formatter.col(-8, margin = 5).col(-7, style = "bold #F00")

	for game in response:
		hTeam = game.teams.home
		vTeam = game.teams.away
		inning = "Final" if game.status.statusCode == "F" else ""
		is_final = bool(inning)
		
		linescore = game.linescore
		if linescore:
			vInnings = []
			hInnings = []
			
			vteamPrefix = ""
			hteamPrefix = ""
			count = ""

			hrowstyle = ""
			vrowstyle = ""
	
			if not is_final:
				inning = f"{linescore.inningHalf} {linescore.currentInningOrdinal}" 
				ballprefix = "<c red>⚾</c red><c #FDD>"

				if linescore.inningHalf == "Bottom":
					hteamPrefix = ballprefix
				elif linescore.inningHalf == "Top":
					vteamPrefix = ballprefix
				
				count = f"<c bg-white black>{linescore.outs}</c bg-white black> {linescore.balls} {linescore.strikes}"
			else:
				vruns = linescore.teams.away.runs or 0
				hruns = linescore.teams.home.runs or 0
				hwinner = True if hruns > vruns else False
				winner_rowstyle = "#F00"
				loser_rowstyle = "#A0"
				hrowstyle = winner_rowstyle if hwinner else loser_rowstyle
				vrowstyle = winner_rowstyle if not hwinner else loser_rowstyle
				
			if hasattr(linescore, "innings"):
				vInnings = list(filter(lambda x: x is not None, [i.away.runs for i in linescore.innings]))
				hInnings = list(filter(lambda x: x is not None, [i.home.runs for i in linescore.innings]))

				totalinnings = max(len(vInnings), len(hInnings))
				totalinnings = max(9, totalinnings)

				vInnings += ["-"] * (totalinnings-len(vInnings))
				hInnings += ["-"] * (totalinnings-len(hInnings))

		
			first = "⚫" if linescore.offense.first else "○"
			second = "⚫" if linescore.offense.second else "○"
			third = "⚫" if linescore.offense.third else "○"

			
			formatter.add_row(vteamPrefix + vTeam.team.name, *vInnings, linescore.teams.away.runs or 0, linescore.teams.away.hits or 0, linescore.teams.away.errors or 0, inning, "", second, "", style = vrowstyle)
			formatter.add_row(hteamPrefix + hTeam.team.name, *hInnings, linescore.teams.home.runs or 0, linescore.teams.home.hits or 0, linescore.teams.home.errors or 0, count, first, "", third, margin_bottom = 2, style = hrowstyle)
		else:
			formatter.add_row(vTeam.team.name)
			formatter.add_row(hTeam.team.name, margin_bottom = 2)

@mlb.collection(value = dag.nab.get("league").leagues, cache = True)
def leagues():
	pass
leagues.resources.label("name").id("id")


@mlb.collection(value = dag.nab.get("divisions").divisions, cache = True)
def divisions():
	pass
divisions.resources.label("name").id("id")


@mlb.collection(value = dag.nab.get("https://statsapi.mlb.com/api/v1/standings?sportId=1&leagueId=103,104").records)
def standings():
	pass


@standings.display
def _display_standings(response, formatter):
	formatter.col(title = "Team").col(title = "W").col(title = "L").col(title = "win%").col(title="GB", style = "bold").col( title = "GP")

	divisions = divisions()

	for division in response:
		divisionname = divisions.find(division.division.id).name
		formatter.add_row(divisionname, style = "aqua bold u", id = "division", margin_top = 1)
		for team in division.teamRecords:
			record = team.leagueRecord
			rowstyle = dbulls_color if "Durham Bulls" in team.team.name else ""
			formatter.add_row(team.team.name, record.wins, record.losses, record.pct, team.gamesBack, record.wins + record.losses + record.ties, style = rowstyle)

		formatter.add_row()


"""
Someday, implement app extending
@mlb.app("ileague", preformatter = this._preformatter)
class InternationalLeague(MLB):
dbulls_color = "#4BF"

def _preformatter(formatter):
	formatter.cstyle(r"Durham Bulls", dbulls_color, prefix = "🐮")
	formatter.cstyle(r"Jacksonville Jumbo Shrimp", "#fcbb9b", prefix = "🦐")
	formatter.cstyle(r"Lehigh Valley IronPigs", "#c2c8ca", prefix = "🐷")
	formatter.cstyle(r"Buffalo Bisons", "#B00", prefix = "🦬")
	formatter.cstyle(r"Scranton/Wilkes-Barre RailRiders", "gold1", prefix = "🦔")


@mlb.arg.Date("day")
@mlb.collection(value = dag.nab.get("schedule?sportId=11&hydrate=linescore(runners)&date={day}&leagueId=117").dates[0].games, display = this._display_games, catch = (IndexError, AttributeError), message = "Date: {day}", cache = resources.status.abstractGameCode == "F")
def games(day = dag.nab.now()):
	pass


@mlb.collection(value = dag.nab.get("https://statsapi.mlb.com/api/v1/standings?sportId=11&leagueId=117,112").records, display = this._display_standings)
def standings():
	pass
"""
