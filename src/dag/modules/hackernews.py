from urllib.parse import urlparse

import dag
from dag import this

from dag.lib.words import quantize_or_ignore



@dag.mod("hn", baseurl = "https://hacker-news.firebaseio.com/v0/", default_cmd = this.topstories, doc="https://github.com/HackerNews/API", response_parser = dag.JSON)
class HackerNews(dag.DagMod):

	@dag.arg("id")
	@dag.cmd()
	def item(self, id):
		return dag.get(f"https://hacker-news.firebaseio.com/v0/item/{id}.json")


	@dag.arg.Int("count", max = 500)
	@dag.resources(launch = "{url}")
	@dag.collection( idx = True, display = this._display_topstories )
	def topstories(self, count = 20):
		story_ids = dag.get("topstories.json")
		urls = [f"https://hacker-news.firebaseio.com/v0/item/{id}.json" for id in story_ids[0:count]]
		return dag.get(urls)


	def _display_topstories(self, response, formatter, data):
		response.reverse() 

		formatter.add_message("Story Title", style = "red")

		for story in response:
			timeinfo = dag.DTime(story.time).from_utc().time_ago()

			years = quantize_or_ignore(timeinfo.years, "year")
			days = quantize_or_ignore(timeinfo.days, "day")
			hours =quantize_or_ignore(timeinfo.hours, "hour")
			minutes = quantize_or_ignore(timeinfo.minutes, "minute")

			domain = urlparse(story.url).netloc

			formatter.col(0, style = "skyblue1", id = "storyinfo", just = str.rjust)

			formatter.add_row(f"{story.title} <c purple>({domain})</c>", style = "orange3", just = str.rjust)
			formatter.add_row(f"{years or days or hours or minutes} ago", f"<c b>{story.descendants} comments</c>", f"{story.score} Points", enum = False, id = "storyinfo", padding_left = 6)


	@topstories("story")
	@dag.cmd()
	def comments(self, story):
		dag.cli.run(f"lynx https://news.ycombinator.com/item?id={story.id}")


	@topstories("story")
	@dag.cmd(display = this._display_zcomments)
	def zcomments(self, story):
		def process_kids(kidIDs, comments):
			kids = dag.get([f"https://hacker-news.firebaseio.com/v0/item/{id}.json" for id in kidIDs])
			comments.update(zip(kidIDs, kids))

			newkidIDs = []
			[newkidIDs.extend(k.kids) for k in kids if k.kids]

			if newkidIDs:
				return process_kids(newkidIDs, comments)

			return comments

		comments = {"story": story}

		if story.kids:
			comments = process_kids(story.kids, comments)

		return comments


	def _display_zcomments(self, response, formatter):
		for k in response['story'].kids:
			breakpoint()
			pass