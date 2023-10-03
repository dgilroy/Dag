import dag
from dag import r_


wknc = dag.app.JSON("wknc", baseurl = "https://wknc.org/", help = "See WKNC songs played at a certain time", dateformat = "%Y-%m-%d")


@wknc.arg.Time("time")
@wknc.DEFAULT.collection(value = dag.nab.get("wp-json/wknc/v1/spins?start={date}+0:00&end={date}+23%3A59&station=1"), cache = dag.args.date.daysago >= 2)
def playlist(time = dag.nab.now(), date: dag.DTime = dag.nab.now()):
	return
	

@playlist.display.MESSAGE("<c>Date: {date}</c>")
def display_playlist(response, formatter, parsed, *, count: int = 10):
	total = count
	bold_idx = 0
	
	#NOTE: WKNC IS ONLY CURRENTLY GIVING 100 RESULTS
	
	formatter.col(0, title = "Title").col(1, title = "Artist").col(2, title = "Date")		

	if parsed.get("time") and response:
		time = parsed.get("time")
		date = parsed.get("date")

		dtime = date | time

		response, nearest_item = dag.dtime.dateslice(response, lamb = r_.start.DTIME.from_utc < dtime, total = total)
		bold_idx = response.index(nearest_item)
		
		"""
		nearest_song = next((song for song in response if dag.DTime(song.start).from_utc < dtime), response[-1])

		nearest_song_index = response.index(nearest_song)
		slice_amt = int(total/2)
		response = response[max(nearest_song_index - slice_amt, 0) : nearest_song_index + slice_amt]
		bold_idx = response.index(nearest_song)
		"""

	total = min(len(response), total)

	for idx in range(0, total):
		song = response[idx]
		title = song.song
		artist =  song.artist
		time =  dag.DTime(song.start).from_utc.strftime("%I:%M %p")
		
		formatter.add_row(title, artist, time, style = "u bold" if idx == bold_idx else "")