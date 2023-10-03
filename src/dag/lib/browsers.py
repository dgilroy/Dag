import abc, shlex, subprocess

DEFAULT = "default"
FIREFOX = "firefox"
CHROME = "chrome"
LYNX = "lynx"


class Browser(abc.ABC):
	cli_name = None

	@classmethod
	@abc.abstractmethod
	def open_via_cli(cls, url):
		raise NotImplementedError("'open_file' not implemented")


class GUIBrowser(Browser):
	@classmethod
	def open_via_cli(cls, url):
		assert cls.cli_name is not None, "Browser class must have a defined cli_name"

		subprocess.run(shlex.split(f"{cls.cli_name} {url}"))

		#subprocess.Popen(shlex.split(f"{cls.cli_name} {url}", posix = True))



class FIREFOX(GUIBrowser):
	cli_name = "firefox.exe"



class CHROME(GUIBrowser):
	cli_name = "chrome.exe"



class LYNX(Browser):
	cli_name = "lynx"

	@classmethod
	def open_via_cli(cls, url):
		subprocess.run(shlex.split(f"lynx {url}", posix = True))



registered_browsers = {}

registered_browsers["FIREFOX"] = FIREFOX
registered_browsers["CHROME"] = CHROME
registered_browsers["LYNX"] = LYNX