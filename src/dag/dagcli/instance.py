import sys, os
from typing import NoReturn, Optional

from dag.util import dagdebug

# Set the breakpoint system to DAGPDB
sys.breakpointhook = dagdebug.set_trace

import dag
from dag.dagcli.controller import DagCLIController
from dag.dagcli.pycmd_view import DagPyCmdCLIView


from dag import exceptions, tempcache, instance



#Byte counter
#from pympler.tracker import SummaryTracker
#tracker = SummaryTracker()

class DagCLIInstance(instance.Instance):
	"""
	This class creates and runs a Dag instance 
	"""

	def __init__(self, passed_args: Optional[list[str]] = None, cwdfile: Optional[str] = None, reloadfile: Optional[str] = None, is_silent: bool = False):
		"""
		This class creates and runs a Dag instance 
		
		:param passed_args: An array of arguments to be passed into Dag instance
		:param cwdfile: The path to be created if/when Dag instance changes directories
		:param reloadfile: The path to be created if/when Dag instance initalizes a reload
		:param is_silent: Tells view whether to output text
		"""
		super().__init__()

		self.passed_args = passed_args or []
		self.cwdfile = cwdfile
		self.reloadfile = reloadfile

		# The view that will interact with the user
		self.view = DagPyCmdCLIView(DagCLIController, self.passed_args, is_silent = is_silent)

		# Stores the initial working directory to compare with when instance ends
		self.initial_cwd = os.getcwd()

		# Stores any args that instance passes if/when it attempts to reload
		self.reload_args = False


	def run_prompt_loop(self) -> NoReturn:
		"""initiates the prompt loop for the instance's view"""

		self.view.run_prompt_loop()		


	def process_reload_exception(self, e: Exception) -> NoReturn:
		"""
		Process information given from reload exception

		:param e: The exception sent when the instance reloads. Its str message will be passed into the next instance
		"""
		
		self.reload_args = e.__str__()


	def run(self) -> NoReturn:
		"""(1) Initiates the prompt loop (2) performs cleanup when the prompt loop ends"""

		try:
			# Initiate and run prompt loop
			with dag.ctx(view = self.view, controller = self.view.controller):
				self.run_prompt_loop()
		except exceptions.DagReloadException as e:
			# Reload args are given via the exception
			self.process_reload_exception(e)
		finally:
			# Shut down the instance
			self.shutdown()


	def record_cwd(self) -> NoReturn:
		"""Write current directory to cwdfile """

		with dag.file.open(self.cwdfile, "w") as file:
			file.write(os.getcwd())


	def record_reload_args(self) -> NoReturn:
		"""Write reload args to reloadfile"""

		with dag.file.open(self.reloadfile, "w") as file:
			file.write(self.reload_args)


	def shutdown(self) -> NoReturn:
		"""
		Performs cleanup when instance ends
		Nested Try/Finally to make sure all run
		"""

		try:
			tempcache.clean()
		finally:
			try:
				# If changed CWD: make a file for bash script to note the change
				if self.initial_cwd != os.getcwd():
					# If a cwdfile is provided: Write the new dir to that file for bash script to read
					if self.cwdfile:
						self.record_cwd()
			finally:
				# If reloading: mark in file for bash script to read
				if self.reloadfile and self.reload_args is not False:
					self.record_reload_args()