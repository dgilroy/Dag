import math, getpass
from typing import Generator

import dag
from dag.util import prompter, mixins

from dag import dagargs
from dag.parser.raw_arg_parser import RawArgParser
from dag.parser.arguments import InputArgument, PrefixedCliArgument, CliArgument, get_arg_prefix_greedy



class InputDagArg(InputArgument, mixins.DagLaunchable):
	def __init__(self, dagarg, incmd, value: object = dag.UnfilledArg):
		super().__init__(dagarg)

		self.dagarg = dagarg
		self.incmd = incmd

		self.rawvalue = value if value is not dag.UnfilledArg else []
		self.value = dag.UnfilledArg
		self.name = self.dagarg.clean_name
		self.raw_name = self.dagarg.name
		self.src = None # Maintains whether value came from CLI, prompt, pipe, etc
		
		self.settings = self.incmd.settings | self.dagarg.settings

		self.shortname = ""
		if dagarg in incmd.dagargs.shortnames.values():
			shortnames = incmd.dagargs.shortnames
			self.shortname = list(shortnames.keys())[[*shortnames.values()].index(dagarg)]


	def _dag_launch_item(self):
		with dag.passexc():
			return dag.getsettings(self.value).launch.format(**self.value)

		return None


	@property
	def joined_value(self):
		return (self.settings.nargs_join or " ").join(self.rawvalue)


	def is_do_nargs_join_before_type(self):
		do_nargs = self.settings.nargs ==1 or ("nargs_join" in self.settings and (isinstance(self.settings.type, (str, int)) or "type" not in self.settings))
		breakpoint(not do_nargs)
		return do_nargs


	def default_value(self, incmd):
		return self.dagarg.get_default(incmd) or incmd.dagcmd.defaults[self.name]


	def prompt_value(self, parsed, prompt = None, show_choices = True, prefill = None, **kwargs):
		if self.settings.get("password"):
			return getpass(self.settings.get("password", "Password") + " (hidden): ") 

		return dag.cli.prompt(prompt or self.settings.prompt, complete_list = self.get_complete_items(self.incmd, parsed) or None, display_choices = show_choices, prefill = prefill or self.settings.prompt_prefill, **kwargs)


	def is_do_prompt(self):
		return (self.settings.get("prompt") or self.settings.get("password")) and self.settings.prompt_if


	def do_completion(self, incmd, parsed):
		completer_items = []
		c = self.get_complete_items(incmd, parsed)
		completer_items.extend(c if getattr(c, "__iter__", None) and not isinstance(c, str) else [c])

		return [ *filter(None, completer_items) ]


	def generate_completion_list(self, pincmd, word, parsed):
		completer_items = []

		prefix = ""

		if pincmd.is_current_short_argname and self.shortname:
			try:
				prefix = word[0:word.index(self.shortname) + 1]
			except ValueError:
				return [], word

		if self and not self.settings.nargs == math.inf: # This lets "echo logs logs l.." keep completing files, since echo's arg is a vararg
			word = " ".join(self.rawvalue)

		# If we have an arg, do its completion
		if self is not None:
			arg_completer_items = self.do_completion(pincmd, parsed)
			completer_items.extend([item for item in arg_completer_items if item is not None])

			word = self.modify_completion_text(word)
		else:
			#breakpoint()
			pass

		if prefix:
			completer_items = [prefix + c for c in completer_items]
			word = prefix + word

		if self and self.settings.modify_completion_text: # used by bash to modify default directory files
			word = self.settings.modify_completion_text(word)

		return completer_items, word


	def process_cli_value(self, value):
		if not self.settings.raw:
			if dag.lib.strtools.is_valid_quoted_string(value):
				value = value[1:-1]

			value = value.replace("\\ ", " ")
		elif self.settings.raw:
			if self.settings.stripquotes and dag.lib.strtools.is_valid_quoted_string(value):
				value = value[1:-1]

		return value


	def expand_parsed(self, parsed):
		return self.dagarg.expand_parsed(parsed, self)


	def get_complete_items(self, incmd, parsed):
		if self.settings.get("choices"):
			return self.settings.choices

		compitems = []

		if (comp := self.dagarg.settings.complete): # using self.dagarg.settings so that bash's default complete doesn't override dagarg's specified complete
			if isinstance(comp, (list, tuple)):
				compitems.extend(comp)
			elif isinstance(comp, str):
				compitems.append(comp)
			elif callable(comp):
				compitems.extend(comp())
			else:
				compitems.extend([*comp])

		try:
			if (comp := self.dagarg.complete(incmd, parsed, self)):
				if isinstance(comp, (list, tuple, type({}.keys()))):
					compitems.extend(comp)
				else:
					compitems.append(comp)
		except Exception as e:
			if dag.ctx.completeline_active:
				breakpoint()
				pass

			pass

		return compitems


	def process_parsed_argval(self, argval):
		self.value = argval
		return self.dagarg.process_parsed_arg(argval)


	def argtype(self, incmd):
		return self.settings.type or dag.get_annotations(incmd.dagcmd.fn).get(self.name)


	def process_incmd(self, incmd):
		return self.dagarg.process_incmd(incmd, self.rawvalue)


	def __repr__(self):
		return dag.format(f"""
<c bg-red black><{object.__repr__(self)}</c>
	name: <c b>{self.name=}</c>
	raw value: <c b>{self.rawvalue=}</c>
	joined value: <c b>{self.joined_value=}</c>
	DagArg: <c b>
	{self.dagarg.settings.__repr__()}</c>
	Type: <c b>{self.dagarg}</c>
<c bg-red black>/ InputDagArg></c>
""")


	@classmethod
	def yield_args(cls, parser: RawArgParser) -> Generator:
		"""
		Yield positional dagargs
		:param parser: The raw arg parser processing the tokens
		:yields: InputDagArgs associated to the given token position
		"""

		# Get the position index based on how many position args have already been parsed
		# d.__class__ == InputDagArg <- These are the ones that aren't positional dagargs (aka: ShortInputDagArg/LongInputDagArg)
		posidx = len([d for d in parser.incmd.inputdagargs.values() if d.__class__ == InputDagArg]) 
		try:
			dagarg = parser.incmd.dagargs.positionalargs[posidx]
			yield cls(dagarg = dagarg, incmd = parser.incmd)
		except IndexError as e:
			raise dag.DagError(f"No positional dagarg found for <c bu>\"{parser.proctokens[0]}\"</c bu> (position {posidx})") from e


	def generate_input_argument(self, parser):
		return self


	def parse(self, parser) -> list[str]:
		tokens = parser.proctokens
		nargs = self.dagarg.settings.get("nargs", 1)

		if not tokens:
			# Not sure what to do if this arises yet
			breakpoint(not dag.ctx.completer_active)
			pass

		value = [tokens.pop(0)]
		nargsidx = 1

		# WHILE tokens exist, the next token isn't a named arg, and we have less than #nargs values: Consume the next token
		while tokens and ((self.incmd.settings.raw or not dagargs.is_named_arg(tokens[0])) and nargsidx < nargs):
			if get_arg_prefix_greedy(tokens[0]) and not self.settings.raw:
				break 
				
			value.append(tokens.pop(0))
			nargsidx += 1

		self.rawvalue = value
		target = self.dagarg.target
		self.incmd.raw_parsed.setdefault(target, [])
		self.incmd.raw_parsed[target].extend(value)
		self.incmd.inputdagargs[target] = self
		self.incmd.dagargsmap[self.dagarg] = self




class LongInputDagArg(InputDagArg, PrefixedCliArgument, prefix = "--"):
	is_start_ignore_when_empty: bool = True

	@classmethod
	def yield_args(cls, parser: RawArgParser) -> Generator:
		token: str = parser.proctokens[0]
		namedargs = parser.incmd.dagargs.namedargs.copy()
		dagarg = namedargs.get(dagargs.clean_name(token))

		# If no dagarg: Search if it's a --no- name
		if not dagarg:
			if token.startswith("--no-") and (negarg := namedargs.get(token.removeprefix("--no-"))) and negarg.settings.negatable:
				dagarg = negarg

		# IF no dagarg: Search if it's using = (e.g.: --height=10)
		if not dagarg:
			if "=" in token and token.count("=") == 1:
				argname, val = token.split("=")
				dagarg = parser.incmd.dagargs.get(argname)

				if dagarg:
					parser.proctokens.pop(0)
					parser.proctokens.insert(0, argname)
					parser.proctokens.insert(1, val)

		if not dagarg:
			dagarg = dagargs.DagArg(token)

		# IF dagarg takes arguments: Pop the arg name from proctokens
		if dagarg.settings.nargs != 0:
			parser.proctokens.pop(0)

		yield cls(dagarg, parser.incmd)



class ShortInputDagArg(InputDagArg, PrefixedCliArgument, prefix = "-"):
	@classmethod
	def yield_args(cls, parser: RawArgParser) -> Generator:
		token = parser.proctokens[0]
		incmd = parser.incmd
		token = token.removeprefix(dagargs.SHORT_NAMED_PREFIX)

		# WHILE the token has characters: Parse the characters into potential dagargs
		while token:
			ch = token[0]
			token = token[1:]
	
			# IF char is a valid shortname: Process the shortname
			if dagarg := incmd.dagargs.shortnames.get(ch):
				# IF nargs is not 0: this isn't a flag, but rather a value-taking arg. The next input will be that arg's value (e.g. -c30 means --c-arg 30 if -c isn't a flag)
				value = ch

				# IF dagarg takes a value: make the value the next proctoken
				if dagarg.settings.nargs != 0:
					# IF token is remaining: Use that as the value for the arg
					if token:
						parser.proctokens[0] = token
					# ELSE, token is exhausted: Remove current shortname from proctokens
					else:
						parser.proctokens.pop(0)
				# ELSE, dagarg is a flag: set up protokens for inputdagarg parser to parse value
				else:
					parser.proctokens.pop(0) # Pop to clear out the existing token 
					parser.proctokens.insert(0, dagargs.SHORT_NAMED_PREFIX + ch) # Insert the current char as a standalone flag

					# IF there are more characters to process: Append them after current flag arg (e.g.: "-ltr" -> "-l -tr")
					if token:
						parser.proctokens.insert(1, dagargs.SHORT_NAMED_PREFIX + token)

				yield cls(dagarg, incmd)

				# IF dagarg takes a value: stop looking for more short dagargs
				if dagarg.settings.nargs != 0:
					break

			# ELSE, char isn't a valid shortname: Complain about it
			else:
				raise dag.DagError(f"<c red>Invalid option: '-{ch}'</c red>")


	@classmethod
	def is_valid_prefixed_arg(cls, token):
		return dagargs.is_short_named_arg(token)

