import importlib, inspect

import dag
from dag import settings

from dag.util.nabbers import NabbableSettings

from dag.dagcmds import DagCmd
from dag.applications import DagApp
from dag.exceptions import DagPlaceholderError



class DefaultDagApp(DagApp):
	def __init__(self, *args, **kwargs):
		with dag.ctx("init_defaultapp"):
			super().__init__(*args, **kwargs)

			self._settings = NabbableSettings() # Resets the settings
			self._settings.setdefault("catch", DagPlaceholderError)
			self._settings.setdefault("baseurl", "")
			self._settings.setdefault("help", "")
			self._settings.setdefault("dateformat", "%Y-%m-%d")
			self._settings.setdefault("use_tempcache", True)

			self.dagcmds.register_child("dagmods")
			self.dagcmds.register_child("dagcmds")
			self.dagcmds.register_child("base_dagcmds")


	def pt_process_completion(self, completion):
		from prompt_toolkit.formatted_text import to_formatted_text

		item = completion.text.strip()
		appinfo = dag.instance.controller.appinfo
		identifier_settings = appinfo.get(item, {})
		colored_identifier_name = dag.instance.view.format(identifier_settings.get("color_name") or item)
		completion.display = to_formatted_text(colored_identifier_name)
		completion.style="bold bg:#000000 fg:" + (identifier_settings.get("color") or "#FFFFFF")
		completion.selected_style="bold fg:#000000 bg:" + (identifier_settings.get("color") or "#BBBBBB")

		return completion


	def add_dagcmd(self, dagcmd: DagCmd, is_default_cmd: bool = False) -> DagCmd:
		# IF appmanager is active: Register the dagcmd with the appmanager
		if dag.ctx.active_appmanager:
			dag.ctx.active_appmanager.process_identifier(dagcmd)

		return super().add_dagcmd(dagcmd, is_default_cmd)


	def get_dagcmd_names(self): # This allows for loading imported dagcmds as well as not-yet-imported dagcmds
		return [*set(self.dagcmds.names() + [*dag.instance.controller.appinfo.keys()])]


	def get_dagcmd(self, cmdname):
		if cmdname not in self.dagcmds:
			try:
				# The act of importing the module will attach any defaultapp cmds to the defaultapp
				dag.instance.controller.appmanager.load_cmd_module(cmdname)
			except ValueError:
				pass

		return super().get_dagcmd(cmdname)



callframeinfo = dag.callframeinfo(inspect.currentframe())
defaultapp = DefaultDagApp("default_app", callframeinfo = callframeinfo)


@defaultapp.cmd.DEFAULT
def default_fn(self, name = "", *args, **kwargs):
	if not isinstance(name, str):
		return name

	return f"Command <c b>\"{name}\"</c> not found"



def get_dagcmd(dagcmd_name):
	global defaultapp

	with dag.catch() as e:
		dagcmd_name = dagcmd_name.replace("_", "-")

	return defaultapp.get_dagcmd(dagcmd_name)


if __name__ == "__main__":
	breakpoint()
	pass