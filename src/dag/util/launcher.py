import shlex, re

import dag
from dag.lib import browsers
from dag.util.mixins import DagLaunchable


def is_url(text):
	return re.match("^https?://", str(text))

 
def launch_url(url):
	from subprocess import run # Import here to speed up import
	
	launcher = dag.get_platform().launcher
	run(shlex.split(f"{launcher} {url}"))


def launch_in_chrome(url):
	browsers.CHROME.open_via_cli(url)


def launch_in_firefox(url):
	browsers.FIREFOX.open_via_cli(url)


def launch_in_lynx(url):
	browsers.LYNX.open_via_cli(url)


def get_item_url(item):
	url = item

	if isinstance(item, DagLaunchable):
		url = item._dag_launch_item()

	elif not isinstance(item, str) or not is_url(item):
		raise dag.DagError(f"Item must be DagLaunchable or a string URL")

	return url



def do_launch(item, browser, return_url = False):
	url = get_item_url(item)

	# If return_url, return URL without launching. Used in DagMods
	if return_url:
		return url

	try:
		if browser == browsers.LYNX:
			launch_in_lynx(url)
		elif browser == browsers.CHROME:
			launch_in_chrome(url)
		else:
			launch_url(url)

		return url
	except OSError as e:
		return print('browser launch command exception: ', e)



class Launch:
	def __init__(self, browser = None):
		self.browser = browser or dag.config.DEFAULT_BROWSER

	def __call__(self, item, browser = None, return_url = False):
		return do_launch(item, browser or self.browser, return_url)

	@property
	def FIREFOX(self): return Launch(browsers.FIREFOX)

	@property
	def CHROME(self): return Launch(browsers.CHROME)

	@property
	def LYNX(self): return Launch(browsers.LYNX)

launch = Launch()