from contextlib import contextmanager
from typing import NoReturn

import dag
from dag import dag_view, dag_controller





class Instance:
	is_cli = False
	
	def __init__(self):
		dag.is_instance_running = True


	def init_view(self):
		return dag_view.DagView()


	def init_controller(self):
		return dag_controller.DagController()


	@contextmanager
	def subinstance(self, view = None, controller = None):
		try:
			oldview = self.view
			oldcontroller = self.controller

			self.view = view or dag_view.NullDagView()
			self.controller = controller or type(self.controller)(is_interactive = False)

			yield

		finally:
			self.view = oldview
			self.controller = oldcontroller


	def run_passed_args(self):
		pass


	def run(self) -> NoReturn:
		"""Populates dag's instance variable"""
		old_instance = dag.instance
		dag.instance = self

		self.run_passed_args()

		with dag.dtprofiler("init_controller"):
			self.controller = self.init_controller()

		with dag.dtprofiler("init_view"):
			self.view = self.init_view()

		try:
			self.do_run()
		finally:
			dag.instance = old_instance