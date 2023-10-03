import re

import dag
from dag import resources


def nba_preformatter(formatter):
	formatter.cstyle(r"CHA", "141", prefix="🐝").cstyle("PHI", "red", prefix="★")


nba = dag.app.JSON("nba", baseurl = "http://data.nba.net/10s/prod/v1/", preformatter = nba_preformatter, dateformat = "%Y%m%d", help = "Get info about NBA Games/Teams")


@nba.arg.Date("day", help = "The date of the games")
@nba.DEFAULT.collection(value = dag.nab.get("{day}/scoreboard.json").games, catch = (ValueError), cache = resources.endTimeUTC)
def games(day = "today"):
	"""View NBA Scores"""
	return
	

@games.display.MESSAGE("Date: {day}")
def display_games(response, formatter):
	formatter.col(style = "bold", margin = 1, after = ":", just = str.rjust).col(style = "bold", margin = 3).col(margin = 1, after = ":", just = str.rjust)
	
	for game in response:
		teams = [game.hTeam, game.vTeam]
		try:
			wTeam = max(teams, key = lambda x: int(x.score))
			lTeam = min(teams, key = lambda x: int(x.score))
		except ValueError:
			wTeam = game.hTeam
			lTeam = game.vTeam

		if game.isGameActivated:
			if game.period.isHalftime:
				game_time = "Halftime"
			else:
				time = game.clock
				if game.period.isEndOfPeriod:
					time = "End"
				game_time = time + " Q" + str(game.period.current)
		elif "endTimeUTC" in game.keys():
			game_time = "Final"
		else:
			game_time = game.startTimeUTC

		formatter.add_row(wTeam.triCode, wTeam.score, lTeam.triCode, lTeam.score, game_time)
		

#@nba.collection(value = this.get_teams(dag.nab.get("calendar.json").startDateCurrentSeason[0:4]).league.standard)
@nba.collection
def teams(self):
	return get_teams(dag.get("calendar.json").startDateCurrentSeason[0:4]).league.standard
teams.resources.label("nickname")		

	
def get_teams(year):
	return dag.get.CACHE(f"{year}/teams.json")