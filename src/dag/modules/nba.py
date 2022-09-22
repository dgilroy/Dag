import re

import dag
from dag import this, resources



@dag.mod("nba", baseurl = "http://data.nba.net/10s/prod/v1/", preformatter = this._preformatter, default_cmd = this.games, dateformat = "%Y%m%d", response_parser = dag.JSON)
class NBA(dag.DagMod):
	"""Get info about NBA Games/Teams"""		

	def _preformatter(self, formatter):
		formatter.cstyle(r"CHA", "141", prefix="🐝").cstyle("PHI", "red", prefix="★")
	

	@dag.arg.Date("day", help = "The date of the games")
	@dag.collection(value = dag.nab.get("{day}/scoreboard.json").games, display = this._display_games, message = "Date: {day}", catch = (ValueError), cache = resources.endTimeUTC)
	def games(self, day = "today"):
		"""View NBA Scores"""
		return
		

	def _display_games(self, response, formatter):
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
			

	@dag.resources(label = "nickname")		
	@dag.collection(value = this._get_teams(dag.nab.get("calendar.json").startDateCurrentSeason[0:4]).league.standard)
	def teams(self):
		return

		
	@dag.cmd(value = dag.nab.get("{year}/teams.json"), cache = True)
	def _get_teams(self, year):
		return
		

	def _display_standings(self, response, formatter):
		breakpoint()
		return response