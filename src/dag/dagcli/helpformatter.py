import inspect

from dag.util import styleformatter
from dag.util import nabbers

from dag.persistence import CacheFile
from dag.dagcmd_exctx import DagCmdExecutionContext


def generate_help_text(	):
	formatter = styleformatter.DagStyleFormatter()
	formatter.add_message("MODULE", margin_bottom = 1)

	dagcmd_documentation = inspect.getdoc(dagcmd.__class__) or dagcmd.settings.help or False
	dagcmd_documentation = f"- {dagcmd_documentation}" if dagcmd_documentation else ""
	formatter.add_row(f"<c bold>{dagcmd.name}</c> {dagcmd_documentation}", padding_left = 6, id = "dagcmdname")
	
	formatter.col(style="lightskyblue1", after = ":", id = "dagcmdinfo").col(style = "b", id = "dagcmdinfo")
	
	if dagcmd.settings.baseurl:
		padleft = 8
		formatter.add_row("Base URL", f"{dagcmd.settings.baseurl}", padding_left = padleft, id = "dagcmdinfo")
		if dagcmd.settings.doc:
			formatter.add_row("API Documentation", f"{dagcmd.settings.doc}", padding_left = padleft, id = "dagcmdinfo")
		formatter.add_row("Response Type", f"{dagcmd.settings.response_parser.__name__}", padding_left = padleft, id = "dagcmdinfo")
		if dagcmd.settings.auth:
			formatter.add_row("Auth", f"{dagcmd.settings.auth.__class__.__name__}", padding_left = padleft, id = "dagcmdinfo")
		
	formatter.add_row()
	
	# Get dagcmds and collections
	collections = sorted(dagcmd.collections.get_collections(), key = lambda x: x.fn_name)				
	dagcmds = [dagcmd for dagcmd in dagcmd.subcmdtable.values() if dagcmd != dagcmd.settings.default_cmd]
	dagcmds = sorted(dagcmds, key = lambda x: x.fn_name)
	dagcmds = [*filter(lambda x: x not in collections, dagcmds)]
	
	# Output Default Command
	if defaultcmd := dagcmd.settings.default_cmd:
		formatter.add_message("DEFAULT COMMAND", margin_bottom = 1)
		formatter = print_command_help(defaultcmd, formatter, default = True)

		if dagcmds:
			formatter.add_row()

	# Output Collection Info
	if collections:
		formatter.add_message(f"Collections", margin_bottom = 1)		
		for coll in collections:
			formatter = print_collection_help(coll, formatter)

	# Output DagCmds Info
	if dagcmds:
		other = "OTHER " if dagcmd.settings.default_cmd else ""
		formatter.add_message(f"{other}COMMANDS", margin_bottom = 1)		
		for dagcmd in dagcmds:	
			formatter = print_command_help(dagcmd, formatter)

	return dag.format(str(formatter))


def print_collection_help(coll, formatter, padding_left = 6):
	collname = coll.fn_name

	# Info related to: CACHEING #
	cacheinfo = "Not Cacheable"
	cachecolor = "deeppink2"

	if coll.settings.get("cache") is not None:
		cacheinfo = "Cacheable [not yet built]"
		cachecolor = "fuchsia"

		exctx = DagCmdExecutionContext(dagcmd = coll, parsed = {})

		if CacheFile.exists_from_dagcmd_exctx(exctx):
			cachecolor = "darkolivegreen1"
			items = coll()
			total = len(items)
			cacheinfo = f"Cached. Total: <c b>{total}</c b>"

	cacheinfo = f"(<c u>{cacheinfo}</c u>)"

	# Info related to: INDEXING #
	indexed = "(Alist)" if coll.settings.idx else ""

	formatter.col(0, style = "b", greedy = False, id = "collinfo").col(2, style = cachecolor, id = "collinfo")
	formatter.add_row(collname, indexed, cacheinfo, padding_left = padding_left, id = "collinfo")


	# Info related to: VALUE #
	value = ""

	formatter.col(0, id = "colsettings", style = "lightskyblue1")
	if val := coll.settings.get("value"):
		if isinstance(val, nabbers.Nabber):
			action = val.__class__.__name__.upper()
			value = f"{action} {coll.dagcmd.settings.baseurl}{val.val}"

		formatter.add_row("Value: ", value, id = "colsettings", padding_left = padding_left + 4, style = "b")

	# Info related to: LABEL #
	label = f"{coll.settings.label}" if coll.settings.get("label") else ""
	if label:
		formatter.add_row("Label: ", label, id = "colsettings", padding_left = padding_left + 4, style = "b")

	formatter.add_row()

	return formatter


def print_command_help(dagcmd, formatter, padding_left = 6, default = False):
	formatter.col(1, "bold")
	dagcmdname = f"({dagcmd.fn_name})" if default else dagcmd.fn_name
	
	dagargcache = ""
	try:
		if dagcmd.settings.get("cache") is not None:
			dagargcache = " <c darkolivegreen1>(<c u>cached</c u>)</c>"
	except Exception:
		# implement checking whether cacheing is a lambda
		breakpoint()
		pass
		
	formatter.add_row(f"{dagcmd.dagcmd.name} <c bold>{dagcmdname}</c> {get_dagargstring(dagcmd)}", padding_left = padding_left)
	
	help_text = (inspect.getdoc(dagcmd.fn) or dagcmd.settings.help or "")
	if help_text:
		formatter.add_row(f"•{help_text}{dagargcache}", padding_left = padding_left + 2, style = "skyblue1")

	for dagarg in dagcmd.dagargs:
		dagargname = f"<{dagarg.__class__.__name__}>" if dagarg.is_positional_dagarg else f"[{dagarg.name}]"
		
		if dagarg.settings.type:
			dagargtype = dagarg.settings.type.__name__
		elif dagarg.settings.flag:
			dagargtype = type(dagarg.settings.flag).__name__
		elif dagargname in dagcmd.defaults:
			dagargtype = type(dagcmd.defaults[dagargname]).__name__
		else:
			dagargtype = "str"

		if dagarg.settings.nargs != 1 and dagargtype == "str":
			dagargtype = str(dagarg.settings.nargs) + dagargtype
			
		dagargprompt = ""
		if dagarg.settings.password:
			dagargprompt = "<c bold underline>(hidden input)</c> <c purple>" if dagarg.settings.prompt else ""
		elif dagarg.settings.prompt:
				dagargprompt = "<c bold underline>(prompted)</c> <c purple>" if dagarg.settings.prompt else ""
			
		dagargflag = " <c underline>flag</c> " if dagarg.settings.flag is not None else ""
		quote = "\"" if dagargtype.endswith("str") else ""
		dagargdefault = f" <c green>default: {quote}{dagcmd.defaults[dagargname]}{quote}</c>" if (dagargname in dagcmd.defaults) else ""

		formatter.add_row(f"<c gold1 bold>{dagarg.name}</c> [{dagargtype}{dagargflag}{dagargdefault}]", padding_left = padding_left + 4, id = "dagarg")
		
		if dagarg.settings.help or dagarg.settings.prompt:
			formatter.add_row(f"{dagargprompt}{dagarg.settings.help or dagarg.settings.prompt}", padding_left = padding_left + 8, id = "info", style = "purple")

		try:
			choices_list = [i for i in dagarg.settings.choices or dagarg.settings.complete or []]
			choices = choices_list[:60]
		except TypeError as e:
			choices = "Choices could not be generated"

		more_choices = f"... Omitting {len(choices_list[60:])} items" if choices_list[60:] else ""
		
		if choices:
			formatter.add_row(f"Choices: <c pink1>{choices}</c><c red bold>{more_choices}</c>", padding_left = padding_left + 4, id = "choices")
		
	if not default:
		formatter.add_row()

	return formatter

		
def get_dagargstring(dagcmd):
	dagargstr = []
	for dagarg in dagcmd.dagargs:
		dagargstr.append(f"<{dagarg.name}>" if dagarg.is_positional_dagarg and (dagarg.clean_name not in dagcmd.defaults) else f"[{dagarg.name}]")
	return "<c sandybrown>{0}</c>".format(" ".join(dagargstr))