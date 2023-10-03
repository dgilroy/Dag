import inspect, json, pprint
from typing import Any
from collections.abc import Callable

import dag
from dag.lib.dot import DotDict
from dag.util.styleformatter import DagStyleFormatter
from dag.util.mixins import DagStyleFormattable
from dag import dagcmds


class InputCommandResponse:
	def __init__(self, incmd, raw_response: object):
		self.incmd = incmd

		# DagCmd's Response
		self.original_response = raw_response					# What the dagcmd returned
		self.original_response_str = str(self.original_response)		

		# A copy of the response for further processing
		self.raw_response = raw_response						# The object after being processed

		# Formatting Response
		self.formatter = DagStyleFormatter()
		self.formatter_fn = self.set_formatter_fn()
		self.formatted_response = ""

		# Response without columns
		self._response_no_multicol = ""

		# The text that goes before/after the response
		self.response_prepension = ""
		self.response_appension = ""


	@property
	def response_no_multicol(self) -> str:
		return self._response_no_multicol or self.response.strip("\n")


	@response_no_multicol.setter
	def response_no_multicol(self, value: str) -> None:
		self._response_no_multicol = value


	@property
	def raw_response_str(self) -> str:
		return str(self.raw_response)


	@property
	def settings(self) -> DotDict:
		try:
			return self.incmd.settings | dag.getsettings(self.raw_response)
		except (AttributeError, TypeError):
			return self.incmd.settings


	@property
	def response(self) -> str:
		return self.response_prepension + str(self.formatted_response or self.raw_response or "") + self.response_appension


	def generate_formatted_response_for_cli(self, parsed) -> None:
		self.formatted_response = self.format_response_for_cli(parsed)


	def append_response(self, text: str) -> None:
		self.response_appension += self.process_pension(text)


	def prepend_response(self, text: str) -> None:
		self.response_prepension += self.process_pension(text)


	def process_pension(self, text: str) -> str:
		return "\n" + str(text).removeprefix("\n").removesuffix("\n") + "\n"


	def set_formatter_fn(self) -> Callable:
		formatfn = lambda x: x

		if formatter := self.settings.display:
			return formatter
		elif isinstance(self.raw_response, DagStyleFormattable):
			return self.raw_response._dag_formatter_fn() or formatfn

		return formatfn



	def __repr__(self) -> str:
		output = dag.format("\n<c darkmagenta u b>>>>>>>>> ICResponse </c>\n")
		output += dag.format(f"""
<c magenta1 u b>>>>>Raw Response </c>\n
{self.raw_response_str}
<c magenta1 u b><<<<Raw Response </c>\n""")

		if self.formatted_response:
			output += dag.format("""
<c magenta1 u b>>>>>Formatted Response </c>\n
{self.formatted_response}
<c magenta1 u b><<<<Formatted Response </c>\n
""")

		output += dag.format("\n<c darkmagenta u b><<<<<<<< ICResponse </c>\n")

		return output


	def format_response_for_cli(self, parsed):
		response = self.raw_response
		incmd = self.incmd

		# IF incmd.settings.display is explicitly False or None: Don't format the output (used when getting alist cmds)
		if "display" in incmd.settings and not incmd.settings.display:
			return self.raw_response

		if response is None:
			return ""		
			
		try:
			formatter = self.formatter or incmd.settings.display
			
			# Get the formatfn's argspec so it's known how many args to pass
			formatfn_argspec = inspect.getfullargspec(self.formatter_fn)
			ismethod = inspect.ismethod(self.formatter_fn)
			total_formatfn_args = len(formatfn_argspec.args) - int(ismethod)

			# Run the DagMod's formatter (is applicable)
			if incmd.dagcmd.settings.get("preformatter"): # Since currently, dagmod formatters excpet DagStyleFormatters
				try:
					# Set up the module formatter
					incmd.dagcmd.settings.preformatter(formatter)
				except AttributeError:
					pass

			displayargs = (response, formatter, dag.DotDict(parsed))[:total_formatfn_args]

			if dag.argspec(self.formatter_fn).kwonlyargs:
				kwonlydict = dag.argspectools.map_argspec_to_parsed(dag.argspectools.kwonlyargspec(self.formatter_fn), parsed)
				formatterresponse = self.formatter_fn(*displayargs, **kwonlydict)
			else:
				formatterresponse = self.formatter_fn(*displayargs)

			response = str(formatterresponse or formatter) # Some formatter_fns may return a string (so resposne) won't be none. Others may work on the formatter and not return anything
			response = "\n" + response.removesuffix("\n") + "\n"

			response = format(response)

			if incmd.settings.prettyprint and not incmd.settings.display: # incmd.settings.display check is so that display fn results don't get overridden
				data = self.raw_response

				while isinstance(data, dag.Response):
					data = data._data

				if isinstance(self.raw_response, dict):
					response = pprint.pformat(data, indent=4, sort_dicts = incmd.settings.sort_dict_response)
				elif isinstance(self.raw_response, dag.mixins.DagJsonEncodable):
					response = pprint.pformat(data, indent=4, sort_dicts = incmd.settings.sort_dict_response)

			return response

		except dag.DagError as e:
			breakpoint()
			pass