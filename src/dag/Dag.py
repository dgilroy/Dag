import sys
from dag.dagcli import instance

# path that will be created if/when Dag instance changes directories
cwdfile = sys.argv[1] if sys.argv[1:2] else None

# path which will store args if/when Dag instance reloads itself
reloadfile = sys.argv[2] if sys.argv[2:3] else None

# The other args passed into the script, to be processed by Dag instance
passed_args = sys.argv[3:] if sys.argv[3:] else []

if "=m" in passed_args:
	import tracemalloc
	tracemalloc.start()
	passed_args.remove("=m")

if __name__ == "__main__":
	instance.DagCLIInstance(passed_args, cwdfile = cwdfile, reloadfile = reloadfile).run()