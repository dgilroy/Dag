import colorsys

import dag
from dag import this


#AUTHENTICATE: https://github.com/Rigellute/spotify-tui
#SECTIONS: https://spotify-audio-analysis.glitch.me/analysis.html
@dag.mod("spotify", color = "#44FF44", auth = dag.auth.OAUTH(this._gat()), baseurl = "https://api.spotify.com/v1/",
			spec = "https://raw.githubusercontent.com/sonallux/spotify-web-api/main/official-spotify-open-api.yml", response_parser = dag.JSON)
class Spotify(dag.DagMod):

	redirect_uri = "http://localhost:8888/callback/"
		
		
	@dag.hook.http_call_fail
	def reset_token(self, response):
		breakpoint()
		# WANT: response code 401 & message 'The access token expired', then reset _gat and somehow have dagmodule know it's been reset
		return response

		
	def _gat(self):
		if not dag.os.has_env("SPOTIFY_REFRESHTOKEN"):
			self.authorize()
			return

		code = dag.env.SPOTIFY_REFRESHTOKEN
		auth = dag.b64.encode(f"{dag.env.SPOTIFY_TOKEN}:{dag.env.SPOTIFY_SEC}")
		headers = {
			"Authorization": f"Basic {auth}",
		}
		
		breakpoint()
		return dag.post("https://accounts.spotify.com/api/token", data = {"grant_type": "authorization_code", "code": code, "redirect_uri": self.redirect_uri}, headers = headers)


	@dag.cmd()
	def authorize(self):
		scope = "user-read-private user-read-playback-state user-modify-playback-state user-read-currently-playing user-library-read streaming app-remote-control user-read-playback-position user-top-read user-read-recently-played playlist-read-collaborative"
		params = {"client_id": dag.env.SPOTIFY_TOKEN, "response_type":"code", "redirect_uri": self.redirect_uri, "scope": scope}
		url_params = dag.http.dict_to_querystring(params)

		dag.launch.CHROME(f"https://accounts.spotify.com/authorize?{url_params}")
		
		
	@dag.arg("artist", nargs = -1, prompt = "Artist name")
	@dag.collection(value = dag.nab.get("search?q={artist}&type=artist").artists.items, cache = True, display = this._display_artist, message = "Artist Search: <c bold>{artist}</c>", doc = "https://developer.spotify.com/console/get-search-item/")
	def artist(self, artist):
		return
		
		
	def _display_artist(self, response, formatter):
		formatter.col(title = "Title").col(title = "Popularity")
		for item in response:
			popularity = item.get("popularity", 0)
			r,g,b = colorsys.hsv_to_rgb((1 - popularity/100) * .5, 1.0, 255)
			color = f"#{int(r):02x}{int(g):02x}{int(b):02x}"
			formatter.add_row(item.name, popularity, style = color)
		
		
	@dag.arg("song", nargs = -1, prompt = "Song to search")
	@dag.resources(label = "{artists[0].name}-{album.name}-{name}")
	@dag.collection(value = dag.nab.get("search?q={song}&type=track").tracks.items, cache = True, display = this._display_songs, message = "Song Search: <c bold>{song}</c>", idx = True)
	def songs(self, song):
		return
		
		
	def _display_songs(self, response, formatter):
		formatter.col(title = "Title").col(title = "Artist").col(title = "Popularity")
		response.sort_by("popularity", reverse = True)
		formatter.add_row() #Blank row
		for item in response:
			popularity = item.get("popularity", 0)
			r,g,b = colorsys.hsv_to_rgb((1 - popularity/100) * .5, 1.0, 255)
			color = f"#{int(r):02x}{int(g):02x}{int(b):02x}"
			formatter.add_row(item.name, ", ".join(artist.name for artist in item.artists), popularity, style = color)
		
		
	@songs('song', prompt = "The ID of the track to get")
	@dag.cmd(value = dag.nab.get('https://api.spotify.com/v1/tracks/{song.id}'), cache = True)
	def track(self, song):
		return
		
		
	@dag.arg("playlist", nargs = -1)
	@dag.cmd(value = dag.nab.get("search?q={playlist}&type=playlist").playlists.items, cache = True, display = this._display_search, message = "Playlist Search: <c bold>{playlist}</c>")
	def playlist(self, playlist = "cool4"):
		return


	@dag.resources(label = "name")
	@dag.collection(value = dag.nab.get("me/playlists"), cache = True)
	def playlists(self):
		return
		
		
	@songs('song', prompt = "The ID of the track to get")
	@dag.cmd(value = dag.nab.get("https://api.spotify.com/v1/audio-analysis/{song.id}"), cache = True)
	def analysis(self, song):
		return