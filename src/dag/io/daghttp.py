import re, urllib, sys

import dag
from dag.io.dagio import IOMethod, IOSession



# Use to implement caching, response parsers, multithread/processing
# PUT THIS BACK IN DAGIO WHEN DONE




class HttpCall(IOSession):
	group = "http"

	def process_settings(self, settings):
		settings.setdefault("response_parser", dag.ctx.active_dagcmd.settings.response_parser or dag.JSON)
		return settings


	def io_session(self):
		return self.settings.get("sess") or session()

	def process_targets(self):
		urls = self.targets
		return [(dag.ctx.active_dagcmd.settings.baseurl or "") + u if not re.search(r'^http.?://', u) else u for u in urls]


	def process_bytes(self, response):
		return bytes(response.content)


	def prepare_response_for_parsing(self, response):
		try:
			return response.text
		except AttributeError:
			return response


	def process_action(self):
		self.action = getattr(self.io_sess.session, self.action_name)		


	def do_action(self, url, **kwargs):
		dag.bb.pre_dagcmd_value()
		if dag.settings.offline:
			dag.echo("<c red u / Dag set to offline: No action taken>")
			return dag.Response("")

		sess = kwargs.get("session", self.io_sess)

		sess.headers.update(kwargs.get("headers", {}))
		sess.params.update({key: str(value) for key, value in kwargs.get("params", {}).items()})
		sess.json = kwargs.get("json", {})
		sess.cookies.update(kwargs.get("cookies", {}))
		sess.data = kwargs.get("data", {})
		sess.proxies.update(kwargs.get("proxies", {}))
		sess.files = kwargs.get("files", [])

		url = dag.hooks.do("process_url", url, sess) or url
		dag.hooks.do("pre_http_call", sess)
		dag.hooks.do(f"pre_http_{self.action_name}", sess)

		auth = dag.ctx.active_dagcmd.settings.auth if not dag.ctx.setting_token else None

		response = self.action(url, json = sess.json or None, data = sess.data, files = sess.files, auth = auth, verify = sess.verify)

		if kwargs.get("pager"):
			kwargs.get("pager").run_pager(url, response)
			breakpoint()
			pass

		status_code = response.status_code

		dag.hooks.do("raw_http_response", response)
		dag.hooks.do(f"raw_http_response_{status_code}", response)
		dag.hooks.do(f"raw_http_{self.action_name}_response", response)
		dag.hooks.do(f"raw_http_{self.action_name}_response_{status_code}", response)

		if response.ok:
			dag.hooks.do("http_call_success", response)
			dag.hooks.do(f"http_call_success_{status_code}", response)
			dag.hooks.do(f"http_{self.action_name}_success", response)
			dag.hooks.do(f"http_{self.action_name}_success_{status_code}", response)
		else:
			dag.hooks.do("http_call_fail", response, kwargs)
			dag.hooks.do(f"http_call_fail_{status_code}", response, kwargs)
			dag.hooks.do(f"http_{self.action_name}_fail", response, kwargs)
			dag.hooks.do(f"http_{self.action_name}_fail_{status_code}", response, kwargs)
			
			if not kwargs.get("ignore_errors", False):
				raise dag.DagError(f"{status_code} {response.reason}\nResponse:\t{response.text}\nURL:\t\t{url}")

		if response is None:
			raise TypeError("Dag HTTP Call Response is None")

		return response


	def after_action_hooks(self, response):
		dag.hooks.do("http_response_object", response)
		dag.hooks.do(f"http_{self.action_name}_response_object", response)
		


get = IOMethod(None, "get", group = "http", session_class = HttpCall)
post = IOMethod(None, "post", group = "http", session_class = HttpCall)
put = IOMethod(None, "put", group = "http", session_class = HttpCall)
delete = IOMethod(None, "delete", group = "http", session_class = HttpCall)
head = IOMethod(None, "head", group = "http", session_class = HttpCall, attr = "headers")




def dict_to_querystring(dic):
	return urllib.parse.urlencode(dic)


def postencode(msg):
	return urllib.parse.quote_plus(msg) # quote_plus encodes form values so that spaces are +'s.


def urlencode(msg):
	return urllib.parse.quote(msg) 		# Turns spaces into %20



def get_file(url, filename, getter = None, directory = ".", **kwargs): # Not sure how to get filename from URL for instances where URL doesn't match download file name, like Vision downloads
	getter = getter or get
	r = getter(url, stream = True, raw = True, **kwargs)

	filepath = dag.Path(directory) / filename
	
	if r.status_code == 200:
		filename = dag.file.filename_avoid_overwrite(filepath)

		with dag.file.open(filename, 'wb') as f:
			for chunk in r.iter_content(1024):
				f.write(chunk)

	return r, filename





class DagHttpSession(dag.DotAccess):
	def __init__(self, *args, **kwargs):
		self.args = args
		self.kwargs = kwargs
		self.session = None
		self.entrances = 0

		
	def __enter__(self):
		import requests # lazy import here because importing requests slows down dag load
		
		if self.session is None:
			self.session = requests.session(*self.args, **self.kwargs)

		self.entrances += 1

		return self


	def __exit__(self, type, value, traceback):
		self.entrances -= 1

		if self.entrances <= 0:	# Set up this way in case session is entered into after started earlier somewhere else (Might not be necessary bc CTXManager is a class, not obj)
			self.session.__exit__()


	def get_file(self, *args, **kwargs):
		return get_file(*args, session = self, **kwargs)


	def __getattr__(self, value, default = None):
		return getattr(sys.modules[__name__], value, default) or getattr(self.session, value, default)



def session(*args, **kwargs):
	return DagHttpSession(*args, **kwargs)



def is_url(text: str) -> re.Match | None:
	return re.match("^(https?|ftp)://", text)


class Pager:
	def __init__(self, datagetter, **params):
		self.datagetter = datagetter
		self.params = params


	def run_pager(self, url, response):
		with dag.ctx(pager_active = True):
			data = dag.drill(response, self.datagetter)
			urls = [url]

			paramvals = {}

			for name, value in self.params.items():
				breakpoint()
				pass

			breakpoint()
			pass



def inputfill_param(infodict):
	value = "{"

	for k,v in infodict.items():
		value += f'"{k}":"{v}",'

	value = "&_InputIdFillValues=" + dag.urlencode(value.rstrip(",") + "}")
	return value