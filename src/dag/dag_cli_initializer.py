import sys, importlib, os

#import gc
#gc.disable() <- can use this if lagging during restarts gets annoying

# path that will be created if/when Dag instance changes directories
cwdfile = sys.argv[1] if sys.argv[1:2] else None

# The other args passed into the script, to be processed by Dag instance
passed_args = sys.argv[2:] if sys.argv[2:] else []

if "=m" in passed_args:
	import tracemalloc
	tracemalloc.start()
	passed_args.remove("=m")


if __name__ == "__main__":
	initial_cwd = os.getcwd()

	try:
		while True:
			from dag.dagcli import instances

			instance = instances.DagCLIInstance(passed_args)
			instance.run()
			passed_args = instance.reload_args.split() if instance.reload_args else []

			import dag
			codepath = dag.CODE_PATH
			del dag
			del instance
			
			for k, v in list(sys.modules.items()):
				if k == "__main__":
					continue

				if (hasattr(v, "__file__") and v.__file__ and v.__file__.startswith(str(codepath))):
					sys.modules.pop(k)

			del instances
	finally:
		if initial_cwd != os.getcwd() and cwdfile:
			with open(cwdfile, "w") as file:
				file.write(os.getcwd())