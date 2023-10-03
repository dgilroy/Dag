import sys, re, os, subprocess, abc, pathlib, shlex
from typing import NoReturn
from subprocess import run, Popen, PIPE

from dag.lib import term


PROGRAM_NAME = "dag"


##PLATFORM
class Platform(abc.ABC):
	"""
	A base class containing info for different platforms (cygwin/windows/unix/etc) 
	"""


	"""	The name of the root directory for the platform's shell	"""
	drive_prefix = ""

	"""	The name of the entity that opens URLs in browser. Default: None """
	launcher = None

	"""	The name of the entity that opens files in their default software. Default: None """
	opener = None


	def is_ansi() -> bool:
		"""
		Indicates whether or not the terminal emulator uses ANSI escape codes

		:returns: A flag indicating whether the terminal uses ANSI escape codes
		"""

		return True

	def is_24b_color() -> bool:
		"""
		Indicates whether or not the platform has 24-bit color depth

		:returns: A flag indicating whether the platform supports 24-bit color
		"""

		return True



	@classmethod
	def open(cls, file: str) -> subprocess.CompletedProcess:
		if cls.opener is None:
			raise AttributeError(f"No opener specified for platform <c b>{cls.__name__}</c>")

		return subprocess.run(shlex.split(f"{cls.opener} {file}"))


	@classmethod
	def launch(cls, url: str) -> subprocess.CompletedProcess:
		"""
		Opens provided URL in the default browser

		:param url: The URL to be opened
		:raises AttributeError: If no launcher has been specified (default), then raise AttributeError
		:returns: The completed process
		"""

		if cls.launcher is None:
			raise AttributeError(f"No launcher specified for platform <c b>{cls.__name__}</c>")

		return subprocess.run(shlex.split(f"{cls.launcher} {url}"))


	@staticmethod
	@abc.abstractmethod
	def clipboard(text: str) -> NoReturn:
		"""
		Places selected text into clipboard

		:param text: The text to be placed into the clipboard
		"""

		raise NotImplementedError("'Copy' not implemented")


	@classmethod
	def run_program_with_file(cls, program: str, path: str, *args) -> subprocess.CompletedProcess:
		"""
		Opens/Starts a file with the desired program

		:param program: The shell name of the program to launch
		:param path: The path of the file to open in the given program
		:param args: Any additional SHELL args to be called when the program is called
		:returns: The completed subprocess 
		"""

		return subprocess.run((program, cls.path_to_native(path)) + args)


	@staticmethod
	def path_is_windows(path: str) -> bool:
		"""
		A simple regex test to see whether path begins like "X:"

		:param path: the path to check
		:returns: A flag indicating whether the path is windows-formatted
		"""

		return re.match("^[a-zA-Z]:", path)


	@staticmethod
	def path_is_unix(path: str) -> bool:
		"""
		A simple regex test to see whether path begins with "/"

		:param path: the path to check
		:returns: True/False whether the path is unix-formatted
		"""

		return re.match("^/", path)


	@staticmethod
	def homepath():
		return pathlib.Path.home()

	@classmethod
	def datapath(cls, program_name):
		raise NotImplementedError("No data directory specified")

	@classmethod
	def configpath(cls, program_name):
		raise NotImplementedError("No config directory specified")

	@classmethod
	def statepath(cls, program_name):
		raise NotImplementedError("No state directory specified")

	@classmethod
	def cachepath(cls, program_name):
		raise NotImplementedError("No cache directory specified")

	@classmethod
	def runtimepath(cls, program_name):
		raise NotImplementedError("No cache directory specified")

	@staticmethod
	def program_name(program_name):
		raise NotImplementedError("Program Name not implemented")








	path_to_native = lambda x: x




####UNIX
class Unix(Platform):
	drive_prefix = "/"
	dirslash = "/"
	launcher = "sensible-browser"
	opener = "open"
	is_unix = True
	is_windows = False

	@classmethod
	def unix_to_win(cls, path: str) -> str:
		"""
		Takes a unix-formatted path and converts to Windows

		:param path: The param to be converted to windows formatting
		:returns: the windows-formatted path
		"""
		return re.sub(rf"{cls.drive_prfix}(.)/", lambda match: r'{}:/'.format(match.group(1).upper()), path).replace("/","\\")


	@classmethod
	def clipboard(cls, text: str, codec: str = "utf-8") -> NoReturn:
		"""
		Places selected text into clipboard in Cygwin

		:param text: The text to be placed into the clipboard
		"""

		try:
			Popen([cls.copier], stdin=PIPE).communicate(bytearray(text, codec))
		except Exception:
			print(f"Make sure '{cls.copier}' is installed.")


	@classmethod
	def xdg_path(cls, varname, defaultdir):
		if XDG := os.environ.get("XDG_CACHE_HOME"):
			return pathlib.Path(XDG)

		return pathlib.Path(defaultdir).expanduser()


	@classmethod
	def cachepath(cls, program_name = ""):
		return cls.xdg_path("XDG_CACHE_HOME", "~/.cache") / cls.program_name(program_name)

	@classmethod
	def datapath(cls, program_name = ""):
		return cls.xdg_path("XDG_DATA_HOME", "~/.local/share") / cls.program_name(program_name)

	@classmethod
	def configpath(cls, program_name = ""):
		return cls.xdg_path("XDG_CONFIG_HOME", "~/.config") / cls.program_name(program_name)

	@classmethod
	def statepath(cls, program_name = ""):
		return cls.xdg_path("XDG_STATE_HOME", "~/.local/state") / cls.program_name(program_name)

	@staticmethod
	def program_name(program_name):
		return program_name

	# May want to overwrite in the future
	@classmethod
	def file_manager(cls, file = "."):
		return cls.launch(file)



class WSL2(Unix):
	drive_prefix = "/mnt/"
	launcher = "wslview"
	opener = "wslview"
	copier = "clip.exe"

	@classmethod
	def path_to_native(cls, path):
		if str(path).startswith("\\\\wsl"):
			return path

		return ("//wsl$/Ubuntu"+ str(path)).replace("/", "\\")





###### CYGWIN
class Cygwin(Unix):
	drive_prefix = "/cygdrive/"
	launcher = "cygstart"
	opener = "cygstart"
	copier = "clip"
	# Implement: Open in browser (cygstart), Copy (currently using Clip)


	@classmethod
	def path_to_windows(cls, path: str) -> str:
		"""
		Takes a cygwin-formatted path and turns it into a windows-formatted path

		:param path: The path to convert
		:returns: A windows-formatted path
		"""

		if cls.path_is_windows(path):
			return path

		try:
			return path.split("/")[2].upper() + ":/" + "/".join(path.split("/")[3:])
		except IndexError:
			return path


	path_to_native = path_to_windows




####WINDOWS
class Windows(Platform):
	dirslash = "\\"
	launcher = "start"
	is_unix = True
	is_windows = False

	@staticmethod
	def program_name(program_name):
		return program_name.capitalize()

	@classmethod
	def roaming(cls):
		return cls.homepath() / "AppData" / "Roaming"

	@classmethod
	def cachepath(cls, program_name):
		return cls.roaming()  / cls.program_name(program_name) /"cache"

	@classmethod
	def datapath(cls, program_name):
		return cls.roaming()  / cls.program_name(program_name) / "data"

	@classmethod
	def configpath(cls, program_name):
		return cls.roaming()  / cls.program_name(program_name) / "config"

	@classmethod
	def statepath(cls, program_name):
		return cls.roaming()  / cls.program_name(program_name) / "state"



platforms = {
	"win32": Windows,
	"cygwin": Cygwin,
	"wsl2": WSL2,
}

##TOOLS
def get_platform() -> Platform:
	"""
	Utility that returns Platform class based on system's platform

	:return: The platform related to the OS running Dag instance
	"""

	if sys.platform in platforms:
		return platforms[sys.platform]

	if "WSL2" in os.uname().release:
		return WSL2

	return Unix


# THIS IS HERE BC HOW WINDOWS GETS TERMINAL DIFFERS FROM HOW UNIX GETS TERMINALS
def get_terminal():
	return term.get_terminal()