import re, urllib, sys
from functools import partial

import dag
from dag.lib import concurrency
from dag.persistence import CacheFile
from dag.responses import parse_response_item, registered_parsers
from dag.io.dagio import IOMethod, IOSession



# Use to implement caching, response parsers, multithread/processing
# PUT THIS BACK IN DAGIO WHEN DONE




class HttpCall(IOSession):
	group = "http"

	def process_settings(self, settings):
		settings.setdefault("response_parser", dag.JSON)
		return settings


	def io_session(self):
		return self.settings.get("sess") or session()

	def process_targets(self):
		urls = self.targets
		return [dag.ctx.active_dagcmd.settings.baseurl + u if not re.search(r'^http.?://', u) else u for u in urls]


	def process_bytes(self, response):
		return bytes(response.content)


	def prepare_response_for_parsing(self, response):
		return response.text


	def process_action(self):
		self.action = getattr(self.io_sess.session, self.action_name)		


	def do_action(self, url, **kwargs):
		sess = self.io_sess

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
put = IOMethod(None, "post", group = "http", session_class = HttpCall)
delete = IOMethod(None, "post", group = "http", session_class = HttpCall)
head = IOMethod(None, "post", group = "http", session_class = HttpCall, attr = "headers")




@staticmethod
def dict_to_querystring(dic):
	return urllib.parse.urlencode(dic)


@staticmethod
def urlencode(msg):
	return urllib.parse.quote_plus(msg)


def get_file(url, filename, **kwargs): # Not sure how to get filename from URL for instances where URL doesn't match download file name, like V downloads
	r = get(url, stream = True, raw = True, **kwargs)

	#filename = None
	
	if r.status_code == 200:
		filename = dag.file.filename_avoid_overwrite(filename)

		with open(filename, 'wb') as f:
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


	def __getattr__(self, value, default = None):
		return getattr(sys.modules[__name__], value, default) or getattr(self.session, value, default)



def session(*args, **kwargs):
	return DagHttpSession(*args, **kwargs)
