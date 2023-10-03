#Settings based on:
#https://clig.dev/#configuration

import configparser
from collections.abc import MutableMapping, Mapping

import dag


#dag.directories.initialize()
CONFIGFILE = dag.directories.CONFIG / "dag.ini"
DEFAULT_SECTION = "dag"

class SettingsContainer(dag.DotAccess, MutableMapping):
	def __init__(self, settings = None):
		self.settings = {k.lower(): v for k,v in (settings or {}).items()}

	def __setitem__(self, key, val):
		self.settings[key.lower()] = val

	def __delitem__(self, key):
		del self.settings[key.lower()]

	def __iter__(self):
		return iter(self.settings)

	def __len__(self):
		return len(self.settings)

	def __getattr__(self, attr):
		return self.get(attr)

	def __getitem__(self, key):
		return self.settings[key]

	def __call__(self, attr):
		return self.get(attr)

	def get(self, attr, default = None):
		return self.settings.get(attr.lower(), default)

	def __or__(self, other):
		return self.settings | other.settings


	def __repr__(self):
		return f"<< {type(self)}: {self.settings=} >"


	def flatten(self):
		values = {}

		for section, settings in self.settings.items():
			if isinstance(settings, Mapping):
				values |= {k:v for k,v in settings.items()}
			else:
				values[section] = settings

		return SettingsContainer(values)

	def get_keys(self):
		return [x.upper() for x in [*self.flatten().keys()]]



defaults = SettingsContainer()


def register_default(name, value, section = DEFAULT_SECTION):
	defaults.setdefault(section, {})[name] = value

register_default("WINDOW_ROWS", 45, "window")
register_default("WINDOW_COLS", 185, "window")
register_default("HISTORY_LENGTH", 500, "history")
register_default("HISTORY_FILE_NAME", "dag-history", "history")
register_default("DAGPDB_HISTORY_FILE_NAME", "dagpdb-history", "history")
register_default("CACHEFILE_EXT", "dagcache", "cache")



def load_configparser():
	if not CONFIGFILE.exists():
		reset_config()

	parser = configparser.ConfigParser()
	parser.read(CONFIGFILE)
	return parser


def reset_config():
	parser = configparser.ConfigParser()

	for section, settings in defaults.items():
		parser[section] = {}
		for name, val in settings.items():
			parser[section][name] = str(val)

	write_config(parser)


def write_config(parser):
	with open(CONFIGFILE, 'w+') as configfile:
		parser.write(configfile)


def load_config():
	parser = load_configparser()

	configsettings = {}

	for section, settings in parser.items():
		configsettings |= {k:(int(v) if dag.strtools.isint(v) else v) for k,v in settings.items()} # Turns integer strings into integers

	return SettingsContainer(configsettings)



session_settings = SettingsContainer()
conf_settings = load_config()

def reload_config():
	global conf_settings
	conf_settings = load_config()

def __getattr__(attr):
	return get(attr)

def get(attr, default = None):
	value = default

	if dag.ctx.active_incmd and dag.ctx.directives.get("otherdirectives") and attr in dag.ctx.directives.otherdirectives:
		value = dag.ctx.directives.otherdirectives[attr]
	elif dag.ctx.active_incmd and attr in dag.ctx.directives and dag.ctx.directives.get(attr) is not None:
		value = dag.ctx.directives[attr]
	elif attr in session_settings and session_settings.get(attr) is not None:
		value = session_settings.get(attr)
	elif (val := dag.getenv("DAG_" + attr.upper().removeprefix("DAG_"))) and val is not None:
		value = val
	elif (val := conf_settings(attr)) and val is not None:
		value = val
	elif (val := defaults.get(attr)) and val is not None:
		value = val

	if (default := defaults.flatten().get(attr)) and default is not None:
		value = type(default)(value)

	return value


_items = dir()

def values():
	return list(set(defaults.get_keys() + session_settings.get_keys() + conf_settings.get_keys()))

def __dir__():
	return list(set(values() + _items + [*dag.ctx.directives.keys()]))