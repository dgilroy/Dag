import os
from typing import NoReturn, Optional


"""
import sys
import importlib.abc
import importlib.util

class MyLoader(importlib.abc.Loader):
	def exec_module(self, module):
		# Perform the actual import
		exec(compile(self.source, module.__file__, 'exec'), module.__dict__)
		
		# Call the hook or perform actions after importing
		module.post_import_hook()

# Custom import hook
class MyImportHook:
	def find_spec(self, fullname, path, target=None):
		# Check if the module has already been imported
		if fullname in sys.modules:
			return None  # Let the default import mechanism handle it
		
		# Create a spec for the module
		spec = importlib.util.spec_from_file_location(fullname, path)
		spec.loader = MyLoader()
		return spec

# Add the custom import hook to sys.meta_path
sys.meta_path.insert(0, MyImportHook())

-> May be used to process modules after importing ot search for app/cmdbuilders
"""




import dag
from dag.dagcli.controller import DagCLIController
from dag.dagcli.pycmd_view import DagPyCmdCLIView
from dag.dagcli.prompttoolkit_view import DagPromptToolkitCLIView
from dag.dagcli import pathinfo


from dag import tempcache, instances, directories



#Byte counter
#from pympler.tracker import SummaryTracker
#tracker = SummaryTracker()
class DagCLIInstance(instances.Instance):
	"""
	This class creates and runs a Dag instance 
	"""

	is_cli = True

	def __init__(self, passed_args: Optional[list[str]] = None, is_silent: bool = False):
		"""
		This class creates and runs a Dag instance 
		
		:param passed_args: An array of arguments to be passed into Dag instance
		:param is_silent: Tells view whether to output text
		"""

		with dag.dtprofiler("init CLI instance"):
			self.passed_args = [*filter(None, passed_args or [])] or []
			self.is_silent = is_silent

			self.viewclass = DagPromptToolkitCLIView

			# Super inits the view/controller
			super().__init__()

			# Stores any args that instance passes if/when it attempts to reload
			self.reload_args = False

			self.initialize()


	def run_passed_args(self):
		# Window Resizing
		if not "==w" in self.passed_args:				# If started with "==w", don't resize the window
			termsize = os.get_terminal_size()
			dag.get_terminal().resize_window(rows = max(dag.settings.WINDOW_ROWS, termsize.lines), cols = max(dag.settings.WINDOW_COLS, termsize.columns))
		else:
			self.passed_args.remove("==w")


		if "==p" in self.passed_args:
			self.viewclass = DagPyCmdCLIView
			self.passed_args.remove("==p")


		if "==D" in self.passed_args:				# If started with "==d", don't resize the window
			dag.debug.DEBUG_MODE = True
			self.passed_args.remove("==D")

		if self.passed_args:						# Any other input text is immediately set to run
			self.controller.run_input_line(" ".join(self.passed_args))



	def init_view(self):
		return self.viewclass(is_silent = self.is_silent)


	def init_controller(self):
		return DagCLIController(is_interactive= True)


	def populate_pathinfo(self):
		if not dag.PATHINFO_PATH.exists():
			pathinfo.reset_pathinfo()


	def initialize(self):
		dag.directories.initialize()
		self.populate_pathinfo()
		

	def run_prompt_loop(self) -> None:
		"""initiates the prompt loop for the instance's view"""

		self.view.run_prompt_loop()		


	def process_reload_exception(self, e: Exception) -> None:
		"""
		Process information given from reload exception

		:param e: The exception sent when the instance reloads. Its str message will be passed into the next instance
		"""
		self.reload_args = e.__str__()


	def do_run(self) -> NoReturn:
		"""(1) Initiates the prompt loop (2) performs cleanup when the prompt loop ends"""

		try:
			# Initiate and run prompt loop
			self.run_prompt_loop()
		except dag.DagReloadException as e:
			# Reload args are given via the exception
			#len({k:v for k,v in sys.modules.items() if hasattr(v, "__file__") and v.__file__ and v.__file__.startswith(str(dag.CODE_PATH))}) -> Gets all dag-loaded modules
			dag.echo("RELOADING DAG")
			self.process_reload_exception(e)
		finally:
			# Shut down the instance
			self.shutdown()



	def shutdown(self) -> None:
		"""
		Performs cleanup when instance ends
		Nested Try/Finally to make sure all run

		NOTE: This is called when an instance ends, not when python execution ends
		A python instance might see multiple dag instances
		"""

		try:
			tempcache.clean()
		except:
			pass