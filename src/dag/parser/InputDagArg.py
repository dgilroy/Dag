from collections.abc import Sequence
import getpass

import dag
from dag.lib import mathtools
from dag.util import prompter

from dag.dagargs import DagArg

class InputDagArg:
	def __init__(self, incmd, value = None, dagarg = None, name = ""):
		self.incmd = incmd
		self.value = value or []
		self.dagarg = dagarg or DagArg(name, incmd.dagcmd, {})
		self.name = self.dagarg.clean_name or name
		self.clean_name = self.dagarg.clean_name or name
		self.raw_name = self.dagarg.name or name
		
		self.settings = self.incmd.settings | self.dagarg.settings


	@property
	def joined_value(self):
		return (self.settings.nargs_join or " ").join(self.value)

	@property
	def handles_arrays(self):
		return self.dagarg.handles_arrays


	def is_do_nargs_join_before_type(self):
		return "nargs_join" in self.settings and (isinstance(self.settings.type, str) or "type" not in self.settings)


	def skip_if_unfilled(self):
		return self.dagarg.skip_if_unfilled()


	def default_value(self):
		return self.incmd.dagcmd.fn_arg_defaults[self.name]


	def prompt_value(self, prompt = None, show_choices = True, prefill = None):
		if self.settings.get("password"):
			return getpass(self.settings.get("password", "Password") + " (hidden): ") 
		else:
			return prompter.prompt(prompt or self.settings.prompt, self.get_complete_items() or None, display_choices = show_choices, prefill = prefill or self.settings.prompt_prefill)


	def is_do_prompt(self):
		return self.settings.get("prompt") or self.settings.get("password")


	def do_completion(self):
		text = self.incmd.tokens[-1:] or ""

		completer_items = []
		c = self.get_complete_items()
		completer_items.extend(c if getattr(c, "__iter__", None) and not isinstance(c, str) else [c])

		return [ *filter(None, completer_items) ]


	def process_string_value(self, value):
		return self.dagarg.process_string_value(value)


	def get_complete_items(self):
		if self.settings.get("choices"):
			return self.settings.choices

		complete = []

		if (comp := self.settings.complete):
			if isinstance(comp, (list, tuple)):
				complete.extend(comp)
			elif isinstance(comp, str):
				complete.append(comp)
			else:
				complete.extend([*comp])

		if (comp := self.dagarg.complete(self.incmd)):
			if isinstance(comp, (list, tuple, type({}.keys()))):
				complete.extend(comp)
			else:
				complete.append(comp)

		return complete


	def modify_completion_text(self, text):
		return self.dagarg.modify_completion_text(text)


	def process_raw_argval(self, *args, **kwargs):
		return self.dagarg.process_raw_argval(*args, **kwargs)


	def parse_parser_value(self, argval):
		if isinstance(argval, str) or not isinstance(argval, Sequence):
			argval = [argval]

		if self.handles_arrays:
			argval = self.process_raw_argval(argval, self.incmd)
		else:
			argval = [self.process_raw_argval(val, self.incmd) for val in argval]

		# If Arg has a type, pass the value into the type
		if argtype := self.settings.type:
			for i in range(len(argval)):
				if argval[i] is not None:
					try:
						if argtype in (int, float):
							argval[i] = argtype(mathtools.eval_math(argval[i]))
						else:
							argval[i] = argtype(argval[i])
							
					except (ValueError, TypeError) as e:
						if self.incmd.complete_active:
							pass
						else:
							raise e

		if isinstance(argval, dag.Resource):
			pass
		elif len(argval) == 1 and (self.settings.get("nargs", 1) == 1 or self.is_do_nargs_join_before_type()):
			try: # Try because Resources have length of 1, and getting [0] from a resource was messing it up
				argval = argval[0]
			except KeyError:
				pass	

		elif not self.is_do_nargs_join_before_type() and self.settings.get("nargs_join") and self.settings.nargs != 1:
			argval = self.settings.nargs_join.join(argval)

		return argval


	def __repr__(self):
		return dag.format(f"""
<c bg-red black><{object.__repr__(self)}</c>
	name: <c b>{self.name}</c>
	value: <c b>{self.value}</c>
	joined value: <c b>{self.joined_value}</c>
	DagArg: <c b>
	{self.dagarg.settings.__repr__()}</c>
	Type: <c b>{self.dagarg}</c>
<c bg-red black>/ InputDagArg></c>
""")