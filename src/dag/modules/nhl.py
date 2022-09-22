import dag
from dag import this, response, resources


@dag.mod("nhl", baseurl = "https://statsapi.web.nhl.com/api/v1/", preformatter = this._preformatter, default_cmd = this.games, launch = "http://www.nhl.com", dateformat = "%Y-%m-%d",
	spec = "https://raw.githubusercontent.com/erunion/sport-api-specifications/master/nhl/nhl.yaml", response_parser = dag.JSON)
class NHL(dag.DagMod):
	"""Gets NHL Info"""

	def _preformatter(self, formatter):
		formatter.cstyle(r"Carolina Hurricanes", "#F00", prefix = "🌀")


	@dag.arg.Date("day")
	@dag.resources(id = "gamePk")
	@dag.collection(value = dag.nab.get("schedule?expand=schedule.linescore&date={day}").dates[0].games, display = this._display_games, catch = (IndexError), message = "Date: {day}", idx = True, cache = resources.status.detailedState.lower() == "final")
	def games(self, day = dag.nab.now()):
		"""See NHL game scores for a given date"""
		return

		
	@games("game")
	@dag.cmd(value = dag.nab.get("https://statsapi.web.nhl.com/api/v1/game/{game.gamePk}/feed/live"), display = this._display_boxscore, cache = response.gameData.status.abstractGameState.lower() == "final")
	def boxscore (self, game):
		"""See the scoring plays for an NHL game"""
		return
		

	# DagCmds should declare their formatters so that (1) no formatter overlap (2) multiple dagcmds can use same formatter
	# @formatter(hook(dagcmd_before_cmdfn = "Date: {day}"), idx = True)
	def _display_boxscore(self, response, formatter):
		home_team = response.liveData.linescore.teams.home
		away_team = response.liveData.linescore.teams.away

		formatter.col(style="bold").col().col(style="bold")
		
		#GOALIES#
		formatter.add_row("<c b u lightgreen>Goalies:</c>", id = "header")
		formatter.col(style="b", id="goalies")
		formatter.add_row("Team", "Name", "Saves", "Even Saves", "PP Saves", "SH Saves", "Save%", style = "red", id = "goalies")
		for team in reversed(response.liveData.boxscore.teams._values()):
			for goalie_id in team.goalies:
				goalie = team.players[f"ID{goalie_id}"]
				gstats = goalie.stats.goalieStats
				formatter.add_row(team.team.triCode, f"{goalie.jerseyNumber} {goalie.person.fullName}", f"{gstats.saves}/{gstats.shots}", f"{gstats.evenSaves}/{gstats.evenShotsAgainst}", f"{gstats.powerPlaySaves}/{gstats.powerPlayShotsAgainst}", f"{gstats.shortHandedSaves}/{gstats.shortHandedShotsAgainst}", f"{round(gstats.savePercentage or 0, 2)}", id = "goalies")
			formatter.add_row()
			
		formatter.add_row()

		#SCORING PLAYS#		
		formatter.add_row("<c b u lightgreen>Scoring Plays:</c>", id = "header")
		current_period = None
		
		for scoring_play in response.liveData.plays.get("scoringPlays", []):
			play = response.liveData.plays.allPlays[scoring_play]
			period = play.about.ordinalNum
			
			if current_period and current_period != period:
				formatter.add_row()
				
			current_period = period
			
			strength = "Empty Net" if play.result.emptyNet else play.result.strength.name
			
			formatter.add_row(play.team.name, f"{play.about.periodTime} {period} ({strength})", play.result.description)
			
		formatter.add_row(margin_bottom = 2)
		
		#TEAM STATS#
		ht = response.liveData.boxscore.teams.home.teamStats.teamSkaterStats
		at = response.liveData.boxscore.teams.away.teamStats.teamSkaterStats
		
		
		formatter.add_row("<c b u lightgreen>STATS:</c>", id = "header")
		formatter.col(id = "stats", style = "bold")
		formatter.add_row("Team", "Blocked", "Faceoff %", "Giveaways", "Hits", "PIM", "PPG", "Shots", "Takeaways", id = "stats", style = "red")

		formatter.add_row(home_team.team.name, ht.blocked, ht.faceOffWinPercentage, ht.giveaways, ht.hits, ht.pim, int(ht.powerPlayGoals), ht.shots, ht.takeaways, id = "stats")
		formatter.add_row(away_team.team.name, at.blocked, at.faceOffWinPercentage, at.giveaways, at.hits, at.pim, int(at.powerPlayGoals), at.shots, at.takeaways, id = "stats")
		formatter.add_row()


	@dag.arg('idx', type = int)
	@dag.cmd(help = "Unimplemented function to view game highlights")
	def highlights(self, idx):
		game = self.games().find(idx)
		breakpoint()


	def _display_games(self, response, formatter):
		formatter.col(style = "bold", margin = 2, just = str.rjust).col(style = "bold", margin = 4).col(margin = 2, just = str.rjust)

		for i, game in enumerate(response):
			teams = [game.teams.home, game.teams.away]
			wTeam = max(teams, key = lambda x: int(x.score))
			lTeam = min(teams, key = lambda x: int(x.score))
			
			if wTeam.score is lTeam.score:
				wTeam = game.teams.home
				lTeam = game.teams.away
				
			linescore = game.linescore
			game_period = int(linescore.currentPeriod)
			
			if game_period == 0:
				game_time = game.gameDate
			elif game_period == 3 and linescore.currentPeriodTimeRemaining == "Final":
				game_time = "Final"
			else:
				game_time = f"{linescore.currentPeriodTimeRemaining} {linescore.currentPeriodOrdinal} Period"
									
			formatter.add_row(wTeam.team.name, wTeam.score,  lTeam.team.name, lTeam.score, game_time)


	@dag.resources(label = "teamName", id = "id")
	@dag.collection(value = dag.nab.get("teams").teams)
	def teams(self):
		"""Return a list of NHL teams"""
		return
		
		
	@dag.resources(label = "name")
	@dag.collection(value = dag.nab.get("divisions").divisions)
	def divisions(self):
		"""Return a list of NHL divisions"""
		return
		

	#@dag.arg.Filter.Resource("division", {"division.name" : "{division}"}, type = Resource("divisions").name)
	#@divisions.Filter("division", **{"division.name": "{division}"})
	@dag.collection(value = dag.nab.get("standings").records, display = this._display_standings, cache = False)
	def standings(self, division = None):
		return
		

	def _display_standings(self, response, formatter):
		formatter.col(title = "Team").col(title = "W").col(title = "L").col(title = "OT").col(style = "bold", title = "Pts").col( title = "GP")

		for division in response:
			formatter.add_row(division.division.name, style = "green bold", id = "division", margin_top = 1)
			for team in division.teamRecords:
				clinch_indicator = f"{team.clinchIndicator} - " if team.clinchIndicator else ""
				
				formatter.add_row(clinch_indicator + team.team.name, team.leagueRecord.wins, team.leagueRecord.losses, team.leagueRecord.ot, team.points, team.leagueRecord.wins + team.leagueRecord.losses + team.leagueRecord.ot)
		

		
	#@dag.argorder() -> Somehow, use this to order resulting table
	@teams("team")
	@dag.collection(display = this._display_playerstats, tempcache = True)
	def playerstats(self, team = "hurricanes"):
		roster = dag.get(f"teams/{team.id}?expand=team.roster").teams[0].roster.roster
		playerURLs = [f"/people/{player.person.id}/stats?stats=statsSingleSeason" for player in roster]
		
		player_stats = dag.get(playerURLs)
		return [p + s for p, s in zip(roster, player_stats)]
		

	def _display_playerstats(self, response, formatter):
		def round2(item):
			try:
				return round(item, 2)
			except Exception:
				return 0
			
		formatter.col(style = "b", id = "goalie").col(style = "b", id = "skater").col(style = "b u", id = "header")
		position_stats = response.partition("position.code")
		
		formatter.add_row("Goalies", id = "header")
		formatter.add_row("Name", "Games", "Starts", "GAA", "GA", "Save%", "Shutouts", "Wins", "Losses", "Even%", "PP%", "SH%", style = "red", id = "goalie")
		
		for g in response.filter(**{"position.code": "G"}).has('jerseyNumber', 'stats[0].splits').sort_by(lambda x: int(x.jerseyNumber)):
		#for g in response.filter(**{"position.code": "G"}).has('jerseyNumber', 'stats[0].splits').sort_by(resources.INT.jerseyNumber):
		#for g in response.filter(**{"position.code": "G"}).has('jerseyNumber', 'stats[0].splits').sort_by(resources.TYPE(int).jerseyNumber):
		#for g in response.filter(**{"position.code": "G"}).has('jerseyNumber', 'stats[0].splits').sort_by(resources(int).jerseyNumber):
		#for g in response.filter(resources.position.code = "G"}).has('jerseyNumber', resources.stats[0].splits).sort_by(resources(int).jerseyNumber):
		#for g in response.filter(dag._.position.code = "G").has(dag._jerseyNumber, dag._.stats[0].splits).sort_by(dag._(int).jerseyNumber):
		#for g in response.filter(_.position.code = "G").has(_jerseyNumber, _.stats[0].splits).sort_by(_(int).jerseyNumber):
		#for g in response.filter(_.position.code == "G").has(_.jerseyNumber, _.stats[0].splits).sort_by(_(int).jerseyNumber):
		#for g in response.filter(_.position.code == "G").has(_.jerseyNumber, _.stats[0].splits).sort_by(_.INT.jerseyNumber):
		#for g in response.filter(dag.r_.position.code == "G").has(dag.r_.jerseyNumber, _.stats[0].splits).sort_by(dag.r_.jerseyNumber.INT())):
		#for g in response.filter(r_.position.code == "G").has(r_.jerseyNumber, r_.stats[0].splits).sort_by(r_.jerseyNumber.INT):
			try:
				stats = g.stats[0].splits[0].stat
			except Exception as e:
				continue
				
			formatter.add_row(f"{g.jerseyNumber} - {g.person.fullName}", stats.games, stats.gamesStarted, round2(stats.goalAgainstAverage), stats.goalsAgainst, stats.savePercentage, stats.shutouts, stats.wins, stats.losses, round2(stats.evenStrengthSavePercentage), round2(stats.powerPlaySavePercentage), round2(stats.shortHandedSavePercentage), id = "goalie")
			
		formatter.add_row("Skaters", id = "header", margin_top = 2)
		formatter.add_row("Name", "G", "Asst", "FaceOff%", "GWG", "Games", "OTG", "PIM", "PPG", "Shifts", "SHG", "Shots", style = "red", id = "skater")
		for player in response.exclude(**{"position.code": "G"}).has('jerseyNumber', 'stats[0].splits').sort_by(lambda x: int(x.jerseyNumber)):
			try:
				p = player
				try:
					stats = p.stats[0].splits[0].stat
				except IndexError as e:
					continue
					

				formatter.add_row(f"{p.jerseyNumber} - {p.person.fullName} ({p.position.code})", stats.goals, stats.assists, stats.faceOffPct, stats.gameWinningGoals, stats.games, stats.overTimeGoals, stats.pim, stats.powerPlayGoals, stats.shifts, stats.shortHandedGoals, stats.shots, id = "skater")
			except:
				breakpoint()
				pass