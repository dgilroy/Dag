import inspect

import dag
from dag.util.styleformatter import DagStyleFormatter
from dag.util.mixins import DagStyleFormattable


class InputCommandResponse:
	def __init__(self, incmd, response, time = 0):
		self.incmd = incmd
		self.execution_time = time

		# DagCmd's Response
		self.original_response = response					# What the dagcmd returned
		self.original_response_str = str(self.original_response)		

		# A copy of the response for further processing
		self.raw_response = response						# The object after being processed
		self._response = self.raw_response_str				# Will either be the raw_response_str, or the formatted response (if applicable)

		# Formatting Response
		self.formatter_fn = lambda x: x
		self.formatted_response = ""

		# Response without columns
		self.response_no_multicol = ""

		# The text that goes before/after the response
		self.response_prepension = ""
		self.response_appension = ""

		self.initialize()


	@property
	def raw_response_str(self):
		return str(self.raw_response)

	@property
	def settings(self):
		try:
			return self.incmd.settings | self.raw_response.settings
		except (AttributeError, TypeError):
			return self.incmd.settings


	@property
	def response(self):
		return self.response_prepension + str(self._response or "") + self.response_appension


	@response.setter
	def response(self, value):
		self._response = value


	def generate_formatted_response_for_cli(self):
		self.formatted_response = self.format_response_for_cli()
		self.response = self.formatted_response


	def append_response(self, text):	
		self.response_appension += self.process_pension(text)


	def prepend_response(self, text):
		self.response_prepension += self.process_pension(text)


	def process_pension(self, text):
		return "\n" + str(text).removeprefix("\n").removesuffix("\n") + "\n"



	def set_formatter_fn(self):
		if formatter := self.incmd.dagcmd.settings.display:
			self.formatter_fn = formatter
		elif isinstance(self.raw_response, DagStyleFormattable):
			self.formatter_fn = self.raw_response._dag_formatter_fn() or self.formatter_fn

		return self.formatter_fn




	def initialize(self):
		self.set_formatter_fn()


	def __repr__(self):
		return dag.format(f"""
<c u b>Incmd: </c>{self.incmd}

<c u b>Raw Response: </c>{self.raw_response_str}


<c magenta1 u b>InCmdResponse Formatted Response:</c> {self.formatted_response}
""")


	def format_response_for_cli(self):
		response = self.raw_response

		if response is None:
			return ""		
			
		try:
			formatter = DagStyleFormatter(self)

			if self.settings.idx:
				formatter.enum_rows = True
			
			# Get the formatfn's argspec so it's known how many args to pass
			formatfn_argspec = inspect.getfullargspec(self.formatter_fn)
			total_formatfn_args = len(formatfn_argspec.args)


			# Run the DagMod's formatter (is applicable)
			if self.incmd.dagcmd.settings.get("preformatter"): # Since currently, dagmod formatters excpet DagStyleFormatters
				try:
					# Set up the module formatter
					self.incmd.dagcmd.settings.preformatter(formatter)
				except AttributeError:
					pass


			# Run the DagCmd's formatter
			if total_formatfn_args == 4:
				response = self.formatter_fn(response, formatter, dag.DotDict(self.incmd.parsed))
			elif total_formatfn_args == 3:
				response = self.formatter_fn(response, formatter)
			else:
				response = self.formatter_fn(response)
				

			response = str(response or formatter) # Some formatter_fns may return a string (so resposne) won't be none. Others may work on the formatter and not return anything
			response = "\n" + response.removesuffix("\n") + "\n"

			response = format(response)

			return response

		except dag.DagError as e:
			breakpoint()
			pass