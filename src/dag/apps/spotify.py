import colorsys

import dag



REDIRECT_URI = "http://localhost:8888/callback/"

#AUTHENTICATE: https://github.com/Rigellute/spotify-tui
#SECTIONS: https://spotify-audio-analysis.glitch.me/analysis.html
spotify = dag.app.JSON("spotify", color = "#44FF44", auth = dag.auth.OAUTH(), baseurl = "https://api.spotify.com/v1/",
			spec = "https://raw.githubusercontent.com/sonallux/spotify-web-api/main/official-spotify-open-api.yml")


@spotify.auth.token
def _gat():
	if not dag.os.has_env("SPOTIFY_REFRESHTOKEN"):
		authorize()
		return

	code = dag.env.SPOTIFY_REFRESHTOKEN
	auth = dag.b64.encode(f"{dag.env.SPOTIFY_TOKEN}:{dag.env.SPOTIFY_SEC}")
	headers = {
		"Authorization": f"Basic {auth}",
	}
	
	return dag.post("https://accounts.spotify.com/api/token", data = {"grant_type": "authorization_code", "code": code, "redirect_uri": REDIRECT_URI}, headers = headers)



	
	
@spotify.hook.http_call_fail_400
def reset_token(response):
	breakpoint()
	# WANT: response code 401 & message 'The access token expired', then reset _gat and somehow have dagmodule know it's been reset
	return response

	
@spotify.cmd
def authorize():
	scope = "user-read-private user-read-playback-state user-modify-playback-state user-read-currently-playing user-library-read streaming app-remote-control user-read-playback-position user-top-read user-read-recently-played playlist-read-collaborative"
	params = {"client_id": dag.env.SPOTIFY_TOKEN, "response_type":"code", "redirect_uri": REDIRECT_URI, "scope": scope}
	url_params = dag.http.dict_to_querystring(params)

	dag.launch.CHROME(f"https://accounts.spotify.com/authorize?{url_params}")
	
	
@spotify.arg.GreedyWords("artist", prompt = "Artist name")
@spotify.collection(value = dag.nab.get("search?q={artist}&type=artist").artists.items, cache = True, doc = "https://developer.spotify.com/console/get-search-item/")
def artist(artist):
	return
	

@artist.display.MESSAGE("Artist Search: <c bold>{artist}</c>",)	
def display_artist(response, formatter):
	formatter.col(title = "Title").col(title = "Popularity")
	for item in response:
		popularity = item.get("popularity", 0)
		r,g,b = colorsys.hsv_to_rgb((1 - popularity/100) * .5, 1.0, 255)
		color = f"#{int(r):02x}{int(g):02x}{int(b):02x}"
		formatter.add_row(item.name, popularity, style = color)
	
	
@spotify.arg.GreedyWords("song", prompt = "Song to search")
@spotify.collection(value = dag.nab.get("search?q={song}&type=track").tracks.items, cache = True)
def songs(song):
	return
songs.resources("song").label("{artists[0].name}-{album.name}-{name}")
	

@songs.display(message = "Song Search: <c bold>{song}</c>")
def display_songs(response, formatter):
	formatter.col(title = "Title").col(title = "Artist").col(title = "Popularity")
	response.sort_by("popularity", reverse = True)
	formatter.add_row() #Blank row
	for item in formatter.idxitems(response):
		popularity = item.get("popularity", 0)
		r,g,b = colorsys.hsv_to_rgb((1 - popularity/100) * .5, 1.0, 255)
		color = f"#{int(r):02x}{int(g):02x}{int(b):02x}"
		formatter.add_row(item.name, ", ".join(artist.name for artist in item.artists), popularity, style = color)
	
	
@songs.op(value = dag.nab.get('https://api.spotify.com/v1/tracks/{song.id}'), cache = True)
def track(song):
	return
	
	
@spotify.arg.GreedyWords("playlist")
@spotify.cmd(value = dag.nab.get("search?q={playlist}&type=playlist").playlists.items, cache = True)
def playlist(playlist = "cool4"):
	return


@playlist.display(message = "Playlist Search: <c bold>{playlist}</c>")
def display_playlist(self, response, formatter):
	pass


@spotify.collection(value = dag.nab.get("me/playlists"), cache = True)
def playlists():
	return
playlists.resources.label("name")
	
	
@songs.op(value = dag.nab.get("https://api.spotify.com/v1/audio-analysis/{song.id}"), cache = True)
def analysis(song):
	return