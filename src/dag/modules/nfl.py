import dag
from dag import this

import re


@dag.mod("nfl", baseurl = "http://www.nfl.com/ajax/", response_parser = dag.XML, preformatter = this._preformatter, default_cmd = this.games)
class NFL(dag.DagMod):
		
	def _preformatter(self, formatter):
		formatter.cstyle("Panthers", "#00D5CA", prefix="🐾").cstyle(r"Car[\W]+", "#00D5CA", ignorecase = True).cstyle(r"Saints", "#D3BC8D").cstyle(r"Buccaneers", "#D50A0A").cstyle(r"Falcons", "#a71930")
		
	
	@dag.arg("--detail", flag = True, type = bool)
	@dag.cmd(value = dag.nab.get("https://feeds.nfl.com/feeds-rs/scores.json"), response_parser = dag.JSON, display = this._display_games)
	def games(self, detail = False):
		"""View scores of this week's games"""
		return
		
		
	def _display_games(self, response, formatter, parsed):
		import math; ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(math.floor(n/10)%10!=1)*(n%10<4)*n%10::4])
		
		formatter.col(style = "bold", just = str.rjust, margin = 2).col(style = "bold").col(just = str.rjust, margin = 2)
		for g in response.gameScores:
			formatter.col(0, before = "").col(2, before = "")
			
			if g.score is None:
				tdict = [{"team": g.gameSchedule.homeTeam, "nn": g.gameSchedule.homeTeam.nick}, {"team": g.gameSchedule.visitorTeam, "nn": g.gameSchedule.visitorTeam.nick}]
				tdict2 = {"ht": g.gameSchedule.homeTeam, "vt": g.gameSchedule.visitorTeam} 
				time = dag.DTime.parse.date(g.gameSchedule.gameTimeEastern).strftime("%I:%M %p")
				phase = g.gameSchedule.gameDate
				
			else:
				tdict = [{"team": g.gameSchedule.homeTeam, "nn": g.gameSchedule.homeTeam.nick, "score": g.score.homeTeamScore.pointTotal or 0}, {"team": g.gameSchedule.visitorTeam, "nn": g.gameSchedule.visitorTeam.nick, "score": g.score.visitorTeamScore.pointTotal or 0}]
				time = g.score.time if not g.score.phase == "FINAL" else ""
				phase = g.score.phase
			
			wt = max(tdict, key = lambda x: int(x.get("score", 0)))
			lt = min(tdict, key = lambda x: int(x.get("score", 0)))
			
			if wt == lt:
				wt = tdict[0]
				lt = tdict[1]
			
			if g.score and g.score.phase.startswith("Q"):
				pos_team_id = g.score.possessionTeamId
				pos_team = 0 if pos_team_id in wt["team"].values() else 2
				formatter.col(pos_team, before = "<c #b67207>🏈</c #b67207>")
				
			formatter.add_row(wt.get('nn').capitalize(), wt.get('score'), lt.get('nn').capitalize(), lt.get('score'), f"{time} {phase}")
			
			if g.score and g.score.phase.startswith("Q") and parsed.get("detail", False):
				formatter.add_row(f"{g.score.possessionTeamAbbr} {ordinal(g.score.down)} and {g.score.yardsToGo} - {g.score.yardline}", padding_left = 2, id = "gameinfo")
			
	
	@dag.arg("year", type = str)
	@dag.arg("week", type = str)
	@dag.collection(value = dag.nab.get("scorestrip?season={year}&seasonType=REG&week={week}").gms.g, display = this._display_games2, message = "<c bold>Week {week}</c>", idx = True)
	def games2(self, year = "2018", week = "5",):
		return 
		
		
	def _display_games2(self, response, formatter):
		# Prints the date of the sunday of the given week
		datestr = response[-4].eid[:-2]
		gamedate = dag.DTime(datestr)

		formatter.add_message(f"Date: {gamedate}")
		
		formatter.col(0, "bold", margin = 2).col(1, "bold", margin = 4).col(2, margin = 2)
		
		for g in response:
			tdict = [{"nn": g.hnn, "score": g.hs}, {"nn": g.vnn, "score": g.vs}]

			wt = max(tdict, key = lambda x: int(x.get("score")))
			lt = min(tdict, key = lambda x: int(x.get("score")))
			
			formatter.add_row(wt.get('nn').capitalize(), wt.get('score'), lt.get('nn').capitalize(), lt.get('score'))