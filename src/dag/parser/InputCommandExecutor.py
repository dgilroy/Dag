from dag.lib import dtime

from dag import tempcache
from dag.parser import InputCommandResponse, DagDirective


def execute(incmd):
	return evaluate(incmd)
	# FORMAT HERE



def evaluate(incmd):
	from dag.parser import InputCommandParser
	
	incmd.reset()
	icp = InputCommandParser.InputCommandParser(incmd)
	icp.parse_incmd_tokens()

	directives = incmd.directives2

	incmd.validate_args_input_formatting()
	incmd.run_parser()

	if metadirectives := directives.get_meta_directives():
		# Run the first meta directive: Cmd tools seem to vary how they handle this, but I like just doing the first one
		metadirective = metadirectives[0]
		breakpoint()
	else:
		return execute_incmd(incmd)



def execute_incmd(incmd):
	directives = incmd.directives2

	[directive.process_incmd(incmd) for directive in directives.get_execution_directives()]


	# IF reading from tempcache and tempcache exists: read response from tempcache
	if directives.tempcache and tempcache.TempCacheFile.exists_from_dagcmd_exctx(incmd):
		run_fn = lambda *args, **kwargs: tempcache.TempCacheFile.read_from_dagcmd_exctx(incmd)
	# Else, get response from dagcmd
	else:
		run_fn = incmd.dagcmd.run_with_parsed if not directives.update_cache else incmd.dagcmd.update_with_parsed


	with dag.tprofiler() as profiler:
		response = run_fn(incmd.parsed)

	ic_response = InputCommandResponse.InputCommandResponse(incmd, response, time = profiler.diff)

	response_directives = {}
	[response_directives.setdefault(directive.priority, []).append(directive) for directive in directives.get_response_directives()]

	for prioritylevel, directivelist in sorted(response_directives.items()):
		for directive in directivelist:
			directive.process_ic_response(ic_response)

	return ic_response