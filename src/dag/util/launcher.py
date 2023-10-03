import shlex, re, pathlib
from subprocess import run

import dag
from dag.util.mixins import DagLaunchable



def get_browser(browser = None):
	if browser is None:
		browser = dag.settings.BROWSER or dag.getenv.BROWSER or ""
	else:
		browser = browser.cli_name

	name = pathlib.Path(browser).name.removesuffix(".exe").upper()

	return dag.browsers.registered_browsers.get(name, dag.browsers.CHROME)


def is_url(text):
	return re.match("^https?://", str(text))

 
def launch_url(url):	
	launcher = dag.get_platform().launcher
	run(shlex.split(f"{launcher} {url}"))


def get_item_url(item):
	url = item

	if isinstance(item, DagLaunchable):
		url = item._dag_launch_item()
	elif not isinstance(url, str):
		with dag.passexc():
			url = dag.getsettings(item).launch
			with dag.passexc():
				url = url.format(**item)

	if not isinstance(url, str) or not is_url(url):
		raise dag.DagError(f"Item must be DagLaunchable or a string URL (received: \"{url}\")")

	return url


def do_launch(item, browser, return_url = False):
	url = get_item_url(item)

	# If return_url, return URL without launching. Used in DagMods
	if return_url:
		return url

	try:
		dag.echo(f"LAUNCHING {url}")

		with dag.hooks.do_pre_post("launch", url, item, items = item):
		#with dag.hooks.do_pre_post("launch"):
			dag.hooks.do("launch", url, item, items = item)
			if browser is not None:
				return browser.open_via_cli(url)
			else:
				launch_url(url)

			return url
	except OSError as e:
		return dag.echo('browser launch command exception: ', e)



class Launcher:
	def __init__(self, browser = None):
		self.browser = get_browser(browser)

	def __call__(self, item, browser = None, return_url = False):
		return do_launch(item, browser or self.browser, return_url)

	@property
	def FIREFOX(self): return type(self)(dag.browsers.FIREFOX)

	@property
	def CHROME(self): return type(self)(dag.browsers.CHROME)

	@property
	def LYNX(self): return type(self)(dag.browsers.LYNX)