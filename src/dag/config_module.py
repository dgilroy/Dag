import sys, configparser

import dag



@dag.arg("name", complete = dag.nab.settings.session_settings.settings.keys())
@dag.cmd("settings")
def sessionsettings(name = None, value = ""):
	if name is None:
		return dag.settings.session_settings.settings

	# IF name is an identifier (from piping): Return its settings 
	if isinstance(name, dag.Identifier):
		return dag.getsettings(name)

	if "=" in name:
		name, value = name.split("=")

	if value == "":
		return (dag.settings.get(name, f"No setting with name \"<c ub / {name}>\" found" ))

	return sessionsettings.set(name, value)



@sessionsettings.cmd("set")
def set_setting(setting, value = ""):
	"""Set a session setting"""
	if "=" in setting and not value:
		setting, value = setting.split("=")

	dag.settings.session_settings[setting] = value
	return f"session setting <c bu>{setting}</c bu> = <c bu>{value}</c bu>"


@dag.arg("setting", complete = dag.nab.settings.session_settings.settings.keys())
@sessionsettings.cmd("unset")
def unset_setting(setting):
	try:
		del dag.settings.session_settings[setting]
		return f"Unset <c bu>{setting}</c bu>"
	except Exception:
		return f"Setting <c bu / {setting}> not found. No action taken."



config = dag.app("config")


@config.cmd.DEFAULT
def show_config():
	return dag.get_editor().open_file(dag.directories.CONFIG / "dag.ini")


@config.arg("--section")
@config.cmd("set")
def _set(name, value = "", section = dag.nab.settings.DEFAULT_SECTION):
	config = dag.settings.load_configparser()

	with dag.passexc(configparser.DuplicateSectionError):
		config.add_section(section)

	config.set(section, name, value)
	dag.settings.write_config(config)
	dag.settings.reload_config()