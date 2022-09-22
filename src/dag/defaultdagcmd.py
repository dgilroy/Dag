import dag

from dag.util.nabbers import NabbableSettings

from dag.dagcmds import DagCmd
from dag.exceptions import DagPlaceholderError



default_dagmod = dag.DagMod()
default_dagmod.settings = NabbableSettings() # Resets the settings
default_dagmod.settings._dag_thisref = default_dagmod


def default_fn(self, name, *args, **kwargs):
	if name.lstrip("-").isdigit():
		return dag.get_dagcmd("_base_cli_commands").alist(name)

	return f"Command <c b>\"{name}\"</c> not found"


class DefaultDagCmd(DagCmd):
	imported_cmds = {}

	def __init__(self):
		with dag.ctx(active_dagcmd = default_dagmod):
			super().__init__(default_fn, NabbableSettings(), dagmod = default_dagmod)

			self.settings.setdefault("catch", DagPlaceholderError)
			self.settings.setdefault("subcmds", {})
			self.settings.setdefault("baseurl", "")
			self.settings.setdefault("help", "")
			self.settings.setdefault("dateformat", "%Y-%m-%d")
			self.settings.setdefault("use_tempcache", True)

			self.subcmdtable.register_child("innercmds")
			self.subcmdtable.register_child("dagmods")
			self.subcmdtable.register_child("dagcmds")
			self.subcmdtable.register_child("base_dagcmds")

			self.subcmdtable = self.subcmdtable
			self.fn = default_fn


	def _get_subcmd(self, attr, idval):
		return idval


default_dagcmd_instance = DefaultDagCmd()


def get_dagcmd(dagcmd_name):
	global default_dagcmd_instance

	if dagcmd_name in default_dagcmd_instance.subcmdtable:
		return default_dagcmd_instance.subcmdtable[dagcmd_name]

	return load_dagcmd(dagcmd_name)

def load_dagcmd(dagcmd_name):
	global default_dagcmd_instance

	dagmodcls = default_dagcmd_instance.imported_cmds[dagcmd_name]
	dagmod = dagmodcls()
	default_dagcmd_instance.subcmdtable.children.dagmods.add(dagmod, dagcmd_name)
	return dagmod




if __name__ == "__main__":
	breakpoint()
	pass