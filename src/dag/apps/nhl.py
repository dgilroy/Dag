import dag
from dag import response, resources, r_

def nhl_preformatter(formatter):
	formatter.cstyle(r"Carolina Hurricanes", "#F00", prefix = "🌀", rowstyle="bg-#19")
	formatter.cstyle(r"New Jersey Devils", "#800", prefix = "😈")
	formatter.cstyle(r"Seattle Kraken", "#68A2B9", prefix = "🐙")
	formatter.cstyle(r"Dallas Stars", "#00B847")


nhl = dag.app.JSON("nhl", baseurl = "https://statsapi.web.nhl.com/api/v1/", preformatter = nhl_preformatter, launch = "http://www.nhl.com", dateformat = "%Y-%m-%d",
	spec = "https://raw.githubusercontent.com/erunion/sport-api-specifications/master/nhl/nhl.yaml", help = "Gets NHL Info", version = 0.3)

"""
with nhl.cstyles as cstyler:
	cstyler.add(r"Carolina Hurricanes", "#F00", prefix = "🌀", rowstyle="bg-#19")
	cstyler.add(r"New Jersey Devils", "#800", prefix = "😈")
	cstyler.add(r"Seattle Kraken", "#68A2B9", prefix = "🐙")
	cstyler.add(r"Dallas Stars", "#00B847")
"""



#ZLC -> zero args, labelled, cached
teams = nhl.collection.GET("teams", r_.teams)
teams.resources("team").label("teamName").id("id").launch(r_.officialSiteUrl)
teams.settings.help = "Return a list of NHL teams"


@nhl.DEFAULT.collection(catch = (IndexError), cache = resources.status.detailedState.lower() == "final").GET("schedule?expand=schedule.linescore&date={day}", r_.dates[0].games)
def games(day: dag.DTime = dag.nab.now()):
	"""See NHL game scores for a given date"""
	return
games.resources("game").id("gamePk")


""" # Messing around with 1-liners for dagcmds/ops with non-arbitrary arguments

#@teams.filter(r_.id == 12).op.collection #-> Test to make it only show up for canes
schedule = teams.op("schedule", default = "hurricanes").collection.ARGS(year = dag.arg[dag.DTime](dag.nab.now().year)).GET("schedule?teamId={team.id}&startDate={startyear}-8-01&endDate={startyear+1}-07-05", r_.dates) 
#schedule = teams | OP("schedule", default = "hurricanes") | COLLECTION() <- (called as a function so that the word itself matches colors with ARGS, GET, etc) | ARGS(year = dag.arg[dag.DTime](dag.nab.now().year)) | GET("schedule?teamId={team.id}&startDate={startyear}-8-01&endDate={startyear+1}-07-05", r_.dates) 
schedule = teams | OP("schedule", default = "hurricanes") | COLLECTION() | ARGS(year = dag.arg[dag.DTime](dag.nab.now().year)) | GET("schedule?teamId={team.id}&startDate={startyear}-8-01&endDate={startyear+1}-07-05", r_.dates) 
schedule | RESOURCES("game") | ID("games[0].gamePk")


schedule = teams | OP("schedule", default = "hurricanes") | COLLECTION | ARGS(year = dag.arg[dag.DTime](dag.nab.now().year))
schedule | GET("schedule?teamId={team.id}&startDate={startyear}-8-01&endDate={startyear+1}-07-05" | r_.dates
schedule | RESOURCES("game", ID = "games[0].gamePk")
"""


#@teams.filter(r_.id == 12).op.collection #-> Test to make it only show up for canes
@teams.op.collection 
def schedule(team = "hurricanes", date: dag.DTime = dag.nab.now()):
	startyear = date.year if date.month >= 8 else date.year - 1

	return dag.get(f"schedule?teamId={team.id}&startDate={startyear}-8-01&endDate={startyear+1}-07-05").dates
schedule.resources("game").id("games[0].gamePk")


@nhl.cmd(cache = response.gameData.status.abstractGameState.lower() == "final").GET("https://statsapi.web.nhl.com/api/v1/game/{game:id}/feed/live")
def boxscore(game: dag.Resource[games, schedule]):
	"""See the scoring plays for an NHL game"""
	return


# DagCmds should declare their formatters so that (1) no formatter overlap (2) multiple dagcmds can use same formatter
# @formatter(hook(dagcmd_before_cmdfn = "Date: {day}"))
@boxscore.display
def display_boxscore(response, formatter):
	home_team = response.liveData.linescore.teams.home
	away_team = response.liveData.linescore.teams.away

	formatter.col(style="bold").col().col(style="bold")
	
	#GOALIES#
	formatter.add_row("<c b u lightgreen>Goalies:</c>", id = "header")
	formatter.col(style="b", id="goalies")
	formatter.add_row("Team", "Name", "Saves", "Even Saves", "PP Saves", "SH Saves", "Save%", style = "#FF0000", id = "goalies")
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
	formatter.add_row("Team", "Blocked", "Faceoff %", "Giveaways", "Hits", "PIM", "PPG", "Shots", "Takeaways", id = "stats", style = "#FF0000")

	formatter.add_row(home_team.team.name, ht.blocked, ht.faceOffWinPercentage, ht.giveaways, ht.hits, ht.pim, int(ht.powerPlayGoals), ht.shots, ht.takeaways, id = "stats")
	formatter.add_row(away_team.team.name, at.blocked, at.faceOffWinPercentage, at.giveaways, at.hits, at.pim, int(at.powerPlayGoals), at.shots, at.takeaways, id = "stats")
	formatter.add_row()



@nhl.cmd(help = "Unimplemented function to view game highlights")
def highlights(idx: int):
	game = games().find(idx)
	breakpoint()


@games.display.MESSAGE("Date: {day}")
def display_games(response, formatter):
	formatter.col(style = "bold", margin = 2, just = str.rjust).col(style = "bold", margin = 4).col(margin = 2, just = str.rjust)

	for game in formatter.idxitems(response):
		teams = [game.teams.home, game.teams.away]
		wTeam = max(teams, key = lambda x: int(x.score))
		lTeam = min(teams, key = lambda x: int(x.score))
		
		if wTeam.score is lTeam.score:
			wTeam = game.teams.home
			lTeam = game.teams.away
			
		linescore = game.linescore
		game_period = int(linescore.currentPeriod)
		
		if game_period == 0:
			game_time = dag.date(game.gameDate).from_utc.format("%Y-%m-%d %I:%M %p")
		elif game_period == 3 and linescore.currentPeriodTimeRemaining == "Final":
			game_time = "Final"
		else:
			game_time = f"{linescore.currentPeriodTimeRemaining} {linescore.currentPeriodOrdinal} Period"
		
		formatter.add_row(wTeam.team.name, wTeam.score, lTeam.team.name, lTeam.score, game_time)


	
divisions = nhl.collection.GET("divisions", r_.divisions)
divisions.resources.label("name")
divisions.settings.help = "Return a list of NHL divisions"


standings = nhl.collection.NO_CACHE.GET("standings", r_.records)

	
@divisions.arg("--division", filter = dag.args.division.name == r_.division.name)
@standings.display
def display_standings(response, formatter, *, division = None):
	formatter.col(title = "Team").col(title = "W").col(title = "L").col(title = "OT").col(style = "bold #F80", title = "Pts").col( title = "GP").col( title = "GF").col( title = "GA")

	response = response.sortby(r_.division.name)
	for division in response:
		formatter.add_row(division.division.name, style = "green bold", id = "division", margin_top = 1)
		for team in division.teamRecords:
			clinch_indicator = f"{team.clinchIndicator} - " if team.clinchIndicator else ""
			
			formatter.add_row(clinch_indicator + team.team.name, team.leagueRecord.wins, team.leagueRecord.losses, team.leagueRecord.ot, team.points, team.leagueRecord.wins + team.leagueRecord.losses + team.leagueRecord.ot, team.goalsScored, team.goalsAgainst)

	formatter.add_row()
	formatter.add_row("Team", "W", "L", "OT", "Pts", "GP", "GF", "GA", style = "red")
	

@teams.op.collection(tempcache = True)
def playerstats(team = "hurricanes"):
	roster = dag.get(f"teams/{team.id}?expand=team.roster").teams[0].roster.roster
	playerURLs = [f"/people/{player.person.id}/stats?stats=statsSingleSeason" for player in roster]
	
	player_stats = dag.get(playerURLs)
	return [p + s for p, s in zip(roster, player_stats)]


#nhl.west_playerstats = nhl.teams.filter(dag.r_.conference.id == 5).op.GET("playerstats")
	

@playerstats.display
def display_playerstats(response, formatter):
	def round2(item):
		try:
			return f"{round(item, 2):.02f}"
		except Exception:
			return 0
		
	formatter.col(style = "b", id = "goalie").col(style = "b", id = "skater").col(style = "b u", id = "header")
	
	formatter.add_row("Goalies", id = "header")
	formatter.add_row("No.", "Name", "Games", "Starts", "GAA", "GA", "Save%", "Shutouts", "Wins", "Losses", "Even%", "PP%", "SH%", style = "#FF0000", id = "goalie")

	for g in response.filter(r_.position.code == "G").has(r_.jerseyNumber, r_.stats[0].splits[0].stat).sortby(r_.jerseyNumber.INT):
		stats = g.stats[0].splits[0].stat	
		formatter.add_row(f"{g.jerseyNumber}", f"{g.person.fullName}", stats.games, stats.gamesStarted, round2(stats.goalAgainstAverage), stats.goalsAgainst, round2(stats.savePercentage), stats.shutouts, stats.wins, stats.losses, round2(stats.evenStrengthSavePercentage), round2(stats.powerPlaySavePercentage), round2(stats.shortHandedSavePercentage), id = "goalie")
		
	formatter.add_row("Skaters", id = "header", margin_top = 2)
	formatter.add_row("No.", "Name", "G", "Asst", "Pts", "FaceOff%", "GWG", "Games", "OTG", "PIM", "PPG", "Shifts", "SHG", "Shots", style = "#FF0000", id = "skater")

	for player in response.filter(r_.position.code != "G").has(r_.jerseyNumber, r_.stats[0].splits[0].stat).sortby(r_.stats[0].splits[0].stat.goals, reverse = True):
		try:
			p = player
			stats = p.stats[0].splits[0].stat					

			formatter.add_row(f"{p.jerseyNumber}", f"{p.person.fullName} ({p.position.code})", stats.goals, stats.assists, stats.goals + stats.assists, round2(stats.faceOffPct), stats.gameWinningGoals, stats.games, stats.overTimeGoals, stats.pim, stats.powerPlayGoals, stats.shifts, stats.shortHandedGoals, stats.shots, id = "skater")
		except:
			breakpoint()
			pass


@schedule.display
def display_schedule(response, formatter, parsed, *, count: int = 10, all: bool = False):
	homewin = "homewin"
	teamwin = "teamwin"
	teamlose = "teamlose"
	awaywin = "awaywin"

	now = dag.now()

	response, nearest_item = dag.dtime.dateslice(response, lamb = r_.games[0].gameDate.DTIME > now, total = count if not all else len(response))

	for game in formatter.idxitems(response):
		rowstyle = "u" if game is nearest_item else ""

		game = game.games[0]
		teams = game.teams
		gamedate = dag.date(game.gameDate)
		datestr = gamedate.from_utc.format("%b %d %Y (%a):")

		if gamedate < now:
			ishomewinning = teams.away.score > teams.home.score
			
			isteamhome = teams.home.team.id == parsed.team.id
			isteamwinning = ishomewinning == isteamhome

			rowid = (homewin if ishomewinning else awaywin) + " "
			rowid += teamwin if isteamwinning else teamlose

			rowstyle += " bg-#200" if isteamwinning else " bg-#030"

			formatter.add_row(datestr, teams.home.team.name, teams.home.score, teams.away.team.name, teams.away.score, id = rowid, style = rowstyle)
		else:
			formatter.add_row(datestr, teams.home.team.name, "", teams.away.team.name, "", style = rowstyle)