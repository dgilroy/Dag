import dag

program_name = "dag"

DATA = dag.get_platform().datapath(program_name)
CONFIG = dag.get_platform().configpath(program_name)
STATE = dag.get_platform().statepath(program_name)
CACHE = dag.get_platform().cachepath(program_name)



def initialize():
	for path in [DATA, CONFIG, STATE, CACHE]:
		# If path doesn't already exist: build it
		if not path.exists():
			path.mkdir(parents = True, exist_ok = True)