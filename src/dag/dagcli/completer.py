import dag
from dag.dagcli import directives


#delimiters = " /"


def complete_dagarg_from_incmd(incmd, debug = False):
	items = []
	dagcmd = incmd.dagcmd

	text = incmd.tokens[-1]

	with dag.ctx(active_dagcmd = dagcmd, parsed = incmd.parsed):
		try:
			# completes with function names if we are completing arg name
			if incmd.is_current_argname():
				items = dagcmd.dagargs.get_named_dagargs_names()
			# Else, assume is a DagArg: Complete DagArg
			else:
				items, text = generate_completion_list_from_dagarg(incmd, text, debug)
		except Exception as e:
			print(dag.echo(f"Completion Error: <c b>{e}</c>"))

	return items, text


def generate_completion_list_from_dagarg(incmd, text, debug = False):
	# List of items to return
	inputarg = incmd.active_inputarg()
	completer_items = []

	# If we have an arg, do its completion
	if inputarg is not None:
		arg_completer_items = inputarg.do_completion()
		completer_items.extend([item for item in arg_completer_items if item is not None])

		text = inputarg.modify_completion_text(text)

	# If there are subcmds, get the dagcmd names
	if incmd.dagcmd and incmd.dagcmd.settings.get("subcmds") and len(incmd.args) <= 1:		#one or fewer args indicates may be typing subcmd name
		completer_items.extend(incmd.dagcmd.settings.subcmds.keys())

	return completer_items, text
	
		
def get_completion_candidates(incmd, debug = False):
	from dag.dagcmds import CollectionDagCmd # Speed up loading dag

	completion_list = []

	text = incmd.tokens[-1] if incmd.tokens else ""

	# If currently is directive: complete directives
	if incmd.is_current_directive():
		return [*DagDirectives.directives.keys()], text
	# Elif currently is a filt on a cached collection: Get collection's keys
	elif incmd.is_current_filt():
		if isinstance(incmd.dagcmd, CollectionDagCmd) and incmd.dagcmd.settings.cache:
			return [f"##{k}" for k in incmd.dagcmd().keys() if f"##{k}".startswith(incmd.tokens[-1])] , text
	elif incmd.is_current_drillbit():
		if isinstance(incmd.dagcmd, CollectionDagCmd) and incmd.dagcmd.settings.cache:
			return [f"::{k}" for k in incmd.dagcmd().keys() if f"::{k}".startswith(incmd.tokens[-1])] , text
	# Else: Complete DagArg
	else:
		# If no dagmod, return nothing. This is currently under is_current_directive so directives will complete (may want to change)
		if not incmd.dagcmd.dagmod:
			return completion_list, text

		# Return completion candidates for current arg
		if incmd.dagcmd:
			items, text = complete_dagarg_from_incmd(incmd, debug)
			completion_list += items

		# Return list of dagcmd names if on first argument
		#if incmd.tokens and incmd.tokens[0].lower() == incmd.dagcmd.dagmod.name and len(incmd.tokens) == 2:
		if incmd.tokens and len(incmd.tokens) == 2:
			completion_list += incmd.subcmdtable.names()
		
	return completion_list, text
	
	
		
def dag_complete_beginning(completion_list, text):
	return [f"{item} " for item in completion_list if item.lower().startswith(text.lower())]
	

def dag_complete_contains(completion_list, text):
	return [item for item in completion_list if text.lower() in item.lower()]

	
def dag_complete(incmd, debug = False):
	completion_list, text = get_completion_candidates(incmd, debug)
	return dag_complete_beginning(completion_list, text) or dag_complete_contains(completion_list, text)