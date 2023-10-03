from urllib.parse import urlparse

import dag

from dag.lib.words import quantize_or_ignore



hn = dag.app.JSON("hn", baseurl = "https://hacker-news.firebaseio.com/v0/", doc="https://github.com/HackerNews/API")

STORYHISTORY = "story-history"

@hn.cmd
def item(id):
	return dag.get(f"https://hacker-news.firebaseio.com/v0/item/{id}.json")


@hn.arg.Int("count", max = 500)
@hn.DEFAULT.collection.NO_CACHE
def topstories(count = 20):
	story_ids = dag.get("topstories.json")
	urls = [f"https://hacker-news.firebaseio.com/v0/item/{id}.json" for id in story_ids[0:count]]
	return dag.get(urls)
topstories.resources("story").launch("{url}")


@topstories.resources.hook.launch
def store_url(url):
	hn.file.append_if_new(STORYHISTORY, url)


@topstories.display
def display_topstories(response, formatter, data):
	history = hn.file.readlines(STORYHISTORY)
	response.reverse() 

	formatter.add_message("Story Title", style = "red")

	for story in formatter.idxitems(response):
		timeinfo = dag.DTime(story.time).from_utc.time_ago()

		years = quantize_or_ignore("year", timeinfo.years)
		days = quantize_or_ignore("day", timeinfo.days)
		hours =quantize_or_ignore("hour", timeinfo.hours)
		minutes = quantize_or_ignore("minute", timeinfo.minutes)

		isread = story.url and story.url in history

		domain = urlparse(story.url).netloc

		READSTYLE = "grey66"

		formatter.col(0, style = "skyblue1" if not isread else READSTYLE, id = "storyinfo", just = str.rjust)
		formatter.col(1, style = "" if not isread else READSTYLE, id = "storyinfo")
		formatter.col(2, style = "" if not isread else READSTYLE, id = "storyinfo")

		formatter.add_row(f"{story.title} <c {'purple' if not isread else READSTYLE}>({domain})</c>", style = "orange3" if not isread else READSTYLE , just = str.rjust)
		formatter.add_row(f"{years or days or hours or minutes} ago", f"<c b>{story.descendants} comments</c>", f"{story.score} Points", enum = False, id = "storyinfo", padding_left = 6)


@topstories.op
def comments(story, firefox: bool = False):
	browser = dag.browsers.FIREFOX if firefox else dag.browsers.LYNX
	browser.open_via_cli(f"https://news.ycombinator.com/item?id={story.id}")


@topstories.op
def zcomments(story):
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


@zcomments.display
def display_zcomments(response, formatter):
	for k in response['story'].kids:
		breakpoint()
		pass