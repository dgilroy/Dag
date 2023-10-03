from __future__ import annotations

import math
from typing import Callable, Generator, Any

import dag
from dag import tempcache
from dag.lib import comparison
from dag.util import drill
from dag.util.drill import DagDrillError

from dag.dagcli import outputprocessors
from dag.exceptions import DagParserError
from dag.parser.inputobjects import InputObject

registered_prefixes = dag.ItemRegistry()




class InputArgument(InputObject):
	"""
	A class that holds an input argument and handles its processing
	"""

	def __init__(self, arg: CliArgument):
		super().__init__(arg)
		self.arg = arg


	def __repr__(self) -> str:
		return dag.format(f"<c bg-#620 black / InputArgument:>\n\t{self.arg}\n<c bg-#620 black / /InputArgument>")




def get_arg_prefix_greedy(text) -> str:
	matches = [prefix for prefix in registered_prefixes if text.startswith(prefix)]
	if matches:
		return sorted(matches, key = len)[-1]

	return ""




def priority(priority: int) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
	"""
	A decorator that adds a priority value to a passed function.
	This is used to determine in which order various incmd/inputarg processing functions get run

	:arg priority: The priority value to assign the wrapped function
	:returns: The wrapped function, updated with a priority value
	"""

	def wrap(fn: Callable[..., Any]) -> Callable[..., Any]:
		"""
		Assigns a priority value to the given function

		:arg fn: The function to wrap
		:returns: The same function now assigned with a priority
		"""

		fn.priority = priority
		return fn

	return wrap




class CliArgument(dag.mixins.CLIInputtable):
	"""
	The model class for the various arguments that are inputted into the CLI
	"""

	@classmethod
	def yield_args(cls: type[CliArgument], parser) -> Generator[CliArgument]:
		"""
		Analyze the tokens and yield however many arguments the current token represents
		e.g. -> "=ur" yields "=u" update directive and "=r" raw directive

		Typically, only one arg will be yielded per token (e.g.: "==raw")

		:param parser: The raw arg parser processing the tokens into arguments
		:yields: The CliArguments associated with the first parser token
		"""

		yield from cls.do_yield_args(parser)


	@classmethod
	def do_yield_args(cls: type[CliArgument], parser) -> Generator[CliArgument]:
		yield cls()


	def parse(self, parser) -> None:
		self.do_parse(parser)


	def do_parse(self, parser, token: str) ->  None:
		pass


	def generate_input_argument(self, parser):
		return InputArgument(self)




class PrefixedCliArgument(CliArgument):
	prefix = None
	is_start_ignore_when_empty = False

	def __init_subclass__(cls, prefix = ""):
		if not prefix:
			raise ValueError("PrefixedCliArgument must be given a prefix")

		cls.prefix = prefix
		registered_prefixes[prefix] = cls


	@classmethod
	def yield_args(cls: type[CliArgument], parser):
		if not parser.proctokens[0].startswith(cls.prefix):
			raise ValueError(f"{cls.__name__} token must start with prefix {cls.prefix}")

		yield from cls.do_yield_args(parser)


	@classmethod
	def is_valid_prefixed_arg(cls, token):
		return True


	def do_parse(self, parser):
		token = parser.proctokens.pop(0)

		# IF name has not already been provided: Infer the name from the token
		if not self.name:
			self.name = token.removeprefix(self.prefix)


	def parse(self, parser) -> None:
		if not parser.proctokens:
			return

		#if not token.startswith(self.prefix):
		#	return tokens

		super().parse(parser)




class SettingsArg(PrefixedCliArgument, prefix = "@@"):
	def process_incmd_meta(self, incmd, parsed):
		if not self.name:
			return dag.getsettings(incmd.active_inputobject)

		return dag.getsettings(incmd.active_inputobject).get(self.name, False) # False because "None" returned from checing incmd meta will make the dagcmd execute


	def get_completion_candidates(self, text, incmd, parsed):
		inobj = incmd.active_inputobject
		settings = dag.getsettings(inobj)
		breakpoint()
		return [self.prefix + k for k in settings.keys()]




class VariableArg(PrefixedCliArgument, prefix = "$$"):
	@priority(math.inf)
	def process_icresponse(self, icresponse):
		if self.name:
			dag.instance.controller.vars[self.name] = icresponse.raw_response
		else:
			breakpoint()
			pass





class DrillArg(PrefixedCliArgument, prefix = "::"):
	drillbit = ""
	is_start_ignore_when_empty = True


	def do_parse(self, parser) -> None:
		token: str = parser.proctokens.pop(0)

		self.drillbit = token.removeprefix(self.prefix)
		self.name = self.drillbit

		if dag.strtools.isint(self.drillbit):
			self.drillbit = f"[{self.drillbit}]"

		elif ":" in self.drillbit and not self.drillbit.startswith("["):
			sli = dag.strtools.strtoslice(self.drillbit)
			self.drillbit = f"[{sli.start or 0}:{sli.stop}:{sli.step or 1}]"


	def get_completion_candidates(self, text, incmd, parsed):
		if incmd.is_cached_collection:
			collection = incmd.dagcmd()

			items = drill.drill_for_properties(collection[0], drillbits = text, approved_initial_properties = [*collection[0]._response._data.keys()], lstrip = ".")
			return [self.prefix + i for i in items]

		return []


	def filter_icresponse(self, icresponse):
		try:
			icresponse.raw_response = drill.drill(icresponse.raw_response, self.drillbit)
		except DagDrillError:
			dag.instance.view.echo(f"Invalid drillbit: {self.drillbit}")



class DirectiveArg(PrefixedCliArgument, prefix = "=="):
	is_start_ignore_when_empty = True

	def __init__(self, name, value, target = ""):
		self.name = name
		self.value = value
		self.target = target or name



	def get_completion_candidates(self, text, incmd, parsed):
		return [self.prefix + d for d in directives.keys()] # Note, prefix is added here due to other prefixed args having possible non-prefixed completion candidates. E.G. ##Filt values



	def __init_subclass__(cls, name: str = "", shortname: str = "", target: str = ""):
		cls.name = name
		cls.shortname = shortname
		cls.target = target or name

		if cls.name:
			directives[name] = cls

		if cls.shortname:
			short_directives[shortname] = cls



	@classmethod
	def get_name_and_value(cls, text, default = True):
		text = text.lstrip(cls.prefix)
		text, value = dag.evaluate_name(text, default)

		return text, value



	def process_value(self) -> object:
		return self.value



	@classmethod
	def do_yield_args(cls, parser):
		name, value = cls.get_name_and_value(parser.proctokens[0])

		if name in directives:
			directive = directives[name]
			yield directive(name, value, directive.target)
		else:
			yield cls(name, value)



	def process_incmd(self, incmd: InputCommand) -> None:
		if self.name in directives:
			incmd.directives[self.target] = self.process_value()
		else:
			incmd.directives.setdefault("otherdirectives", dag.DotDict())
			incmd.directives.otherdirectives[self.name] = self.process_value()
#<<<< DirectiveArg




#>>>> ShortDirectiveArg
class ShortDirectiveArg(PrefixedCliArgument, prefix = "="):
	is_start_ignore_when_empty = True


	@classmethod
	def do_yield_args(cls, parser):
		token: str = parser.proctokens[0]
		token = token.removeprefix(cls.prefix)

		value = True # Used to keep track of whether or not to negate the flag
		for ch in token:
			# If char is "!": flip the boolean value
			if ch == "!":
				# One ! turns on "False", second one turns on "True", etc
				value = not value
				continue

			# IF this is a valid short directive: 
			if directive := short_directives.get(ch):
				# If this is a negated directive, the value will equal 2
				yield short_directives[ch](directive.name, value, directive.target)
			else:
				if dag.ctx.completeline_active:
					raise DagParserError(f"<c b>\"{ch}\"</c b> is not a valid short directive name")

			value = True


	def process_incmd(self, incmd: InputCommand):
		breakpoint()
		pass
#<<<< ShortDirectiveArg


#>>>> OutputDirectiveArg
class OutputDirectiveArg(PrefixedCliArgument, prefix = ">"):
	"""
	This arg, if found, writes the output to a file (if a filename is provided), or otherwise copies it to the clipboard
	"""

	# A flag indicating whether or not the output should be copied to the clipboard
	do_copy: bool = False

	# The name if the file to write to (If applicable)
	outfile_name: str = ""


	def do_parse(self, parser) -> None:
		"""
		Check whether or not the output should be copied to the clipboard or written to a file

		:param parser: The RawArgParser that is assigning tokens to args
		"""

		tokens = parser.proctokens
		token = tokens.pop(0)

		# If ">" was the final token: Do Copy
		if not tokens:
			self.do_copy = True 
		# Else, some tokens follow the ">": Treat the next token as the filename
		else:
			self.outfile_name = tokens.pop(0)


	def process_incmd(self, incmd: InputCommand) -> None:
		"""
		Set up the incmd so that it either copies output or writes it to a file

		:param incmd: The InputCommand to update
		"""

		if self.do_copy:
			incmd.outputprocessor = outputprocessors.ClipboardOutputProcessor(incmd)
		else:
			incmd.outputprocessor = outputprocessors.FileOutputProcessor(incmd, self.outfile_name)
#<<<< OutputDirectiveArg



class FileAppendDirectiveArg(PrefixedCliArgument, prefix = ">>"):

	def do_parse(self, parser):
		if not parser.proctokens:
			raise ValueError("Must enter file for appending")
		else:
			self.outfile_name = parser.proctokens.pop(0)


	def process_incmd(self, incmd: InputCommand):
		incmd.outputprocessor = outputprocessors.FileAppendOutputProcessor(incmd, self.outfile_name)




#>>>>>> Directives
# Holds the long-style directives recognized by dag (e.g.: "==update")
directives = {}

# Holds the short-style directives recognized by dag (e.g.: "=u")
short_directives = {}



### RESPONSE DIRECTIVES ###
class SizeDirective(DirectiveArg, name = "size", shortname = "s"):
	@priority(20)
	def process_icresponse(self, icresponse):
		#icresponse.raw_response = len(icresponse.raw_response)
		#return
		try:
			icresponse.append_response(f"\n\n<c bold>Size:</c>{len(icresponse.raw_response)}")
		except (AttributeError, TypeError) as e:
			icresponse.append_response(f"\n\n<c bold>Cannot get response's size: {e}</c>")




class KeysDirective(DirectiveArg, name = "keys", shortname = "k"):
	@priority(20)
	def process_icresponse(self, icresponse):
		#icresponse.raw_response = icresponse.raw_response.keys()
		#return
		try:
			icresponse.append_response(f"\n\n<c bold>Keys:</c>{[k for k in icresponse.raw_response.keys()]}")
		except AttributeError:
			icresponse.append_response(f"\n\n<c bold>Cannot get response's keys.</c>");



class ChoicesDirective(DirectiveArg, name = "choices", shortname = "c"):
	@priority(20)
	def process_icresponse(self, icresponse):
		#icresponse.raw_response = ic_response.raw_response.choices() or "None"
		#return
		try:
			choices = icresponse.raw_response.choices() or "None"
			icresponse.append_response(f"\n\n<c bold>Choices/Labels:</c>{choices}")
		except (AttributeError, TypeError) as e:
			icresponse.append_response(f"\n\n<c bold>Cannot get labels for response: {e}</c>")



class TimerDirective(DirectiveArg, name = "timer", shortname = "i"):
	starttime = 0

	@priority(20)
	def process_incmd(self, incmd: InputCommand):
		self.starttime = dag.current_micro_time()

	def process_icresponse(self, icresponse):
		self.endtime = dag.current_micro_time()
		diff = (self.endtime - self.starttime)

		icresponse.append_response(f"<c b u>Execution time: {dag.dtime.humanize_microseconds(diff)}</c b u>")



class EditorDirective(DirectiveArg, name = "editor", shortname = "e"): 													# META
	def process_incmd_meta(self, incmd: InputCommand, parsed):
		return dag.get_dagcmd("editor")(incmd.active_identifier)



class HelpDirective(DirectiveArg, name = "help", shortname = "h"):														# META
	def process_incmd_meta(self, incmd: InputCommand, parsed):
		return dag.instance.controller.help(incmd.active_identifier)



class DocumentationDirective(DirectiveArg, name = "documentation", shortname = "d"):									# META
	def process_incmd_meta(self, incmd: InputCommand, parsed):
		return dag.get_dagcmd("documentation")(incmd.active_identifier)



class VersionDirective(DirectiveArg, name = "version", shortname = "v")		:											# META
	def process_incmd_meta(self, incmd: InputCommand, parsed):
		identifier = incmd.active_identifier
		settings = dag.getsettings(identifier)

		identifierpath = settings.copyrightname or identifier.cmdpath()
		version = settings.version
		copyright = settings.copyright or ""
		is_print_verion = not(version is None and not copyright)

		return f"{identifierpath} {version}\n{copyright}" if is_print_verion else f"No version detected for <c bu/{identifierpath}>"



class TempcacheDirective(DirectiveArg, name = "tempcache", shortname = "t"):											# EXECUTION
	@priority(30)
	def process_icresponse(self, icresponse):
		if icresponse.incmd.do_read_from_tempcache:
			breakpoint()
			ic_response.prepend_response("<c red/Reading from tempcache>\n----------------------------\n\n")



class AsyncDirective(DirectiveArg, name = "async", shortname = "a", target = "run_async"): pass									# EXECUTION
class BreakpointDirective(DirectiveArg, name = "breakpoint", shortname = "b", target = "do_dagcmd_breakpoint"): pass			# EXECUTION
class DebugDirective(DirectiveArg, name = "debug", shortname = "D"): pass														# EXECUTION
class ForceDirective(DirectiveArg, name = "force", shortname = "f"): pass														# EXECUTION
class OfflineDirective(DirectiveArg, name = "offline", shortname = "o"): pass													# EXECUTION
class QuietDirective(DirectiveArg, name = "quiet", shortname = "q", target = "silent"): pass									# EXECUTION
class RawDirective(DirectiveArg, name = "raw", shortname = "r", target = "noformat"): pass										# EXECUTION
class UpdateCacheDirective(DirectiveArg, name = "update_cache", shortname = "u", target = "update_dagcmd_cache"): pass			# EXECUTION
class UpdateAllCachesDirective(DirectiveArg, name = "update_all_cache", shortname = "U", target = "update_all_caches"): pass	# EXECUTION
class YesDirective(DirectiveArg, name = "yes", shortname = "y", target = "force"): pass											# EXECUTION
class NoCTagDirective(DirectiveArg, name = "noctags", shortname = "z"): pass													# EXECUTION



#<<<< Directives
#a - async
#b - breakpoint
#c - choices
#d - documentation
#D - Debug
#e - editor
#f - force
#g
#h - help
#i - timer
#j
#k - keys
#l
#m
#n
#o - offline
#p
#q - quiet
#s - size
#t - tempcache
#u - updatecache
#v - version
#w
#x
#y - force (yes)
#z - noctags