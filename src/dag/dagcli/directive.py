import abc, inspect, collections

import dag
from dag.util import dagdebug

directives = {}
directive_prefix = "=="

short_directives = {}
short_directive_prefix = "="


#EXECUTION DIRECTIVES
# (DO EVAL) modify execution ctx: update/raw/debug/timer/async/tempcache

# META DIRECTIVES
# (DONT EVAL) Directly Affect which response: @@settings/help/baseurl
# (DONT EVAL) Get info about first preceding with appropriate info: documentation/editor
				# Maybe @@ by itself just returns whichever dagmod/dagcmd/dagarg precedes it

# RESPOSNE DIRECTIVES
# (MAYBE EVAL) Modify existing response: keys/choices/size/##filts/::drillers/launch/portalurl/Resource directive (replacing dagarg)

# have directives registered as incmd objects. @@ can operate on directives if applicable



# Decorator used to register directives
class directive:
	def __init__(self, long_name, short_name):
		self.long_name = long_name
		self.short_name = short_name

	def __call__(self, parent):
		directives[directive_prefix + self.long_name] = parent
		short_directives[self.short_name] = parent
		return parent





class DirectiveList(collections.UserList):
	def add_if_valid(self, directive = None):
		if directive is None:
			return

		assert issubclass(directive, DagDirective), "Item must be DagDirective"

		if directive not in [d.__class__ for d in self.data]:
			self.data.append(directive())


class DirectiveListExecutor:
	def __init__(self, incmd):
		self.incmd = incmd
		
		self.directivelist = self.incmd.directivelist

		# Filled by preprocessor
		self.run_incmd = None
		self.run_formatter = None



	def preprocess_incmd_directives(self):
		# Have these initially set to false (unless the directive list is empty, then we will be running/formatting)
		# Done here to give directivelist the chance to populate
		self.run_incmd = False or not self.directivelist
		self.run_formatter = False or not self.directivelist

		for directive in self.directivelist:
			self.run_incmd_bool = self.run_incmd or directive.RUN_INCMD
			self.formatter_bool = self.run_formatter or directive.RUN_FORMATTER

			directive.preprocess_incmd(self.incmd)


	def process_ic_response_directives(self, ic_response):
		for directive in self.directivelist:
			directive.process_ic_response(ic_response)



class DagDirective(abc.ABC):
	RUN_INCMD = True
	RUN_FORMATTER = True

	@abc.abstractmethod
	def preprocess_incmd(incmd):
		raise NotImplementedError

	@abc.abstractmethod
	def process_ic_response(ic_response):
		raise NotImplementedError


class DagDirectiveDontRun(DagDirective):
	RUN_INCMD = False
	RUN_FORMATTER = False


@directive("editor", "e")
class Directive_Sublime(DagDirectiveDontRun):
	def __init__(self):
		self.filepath = None
		self.lineno = 0

	def preprocess_incmd(self, incmd):
		self.filepath = inspect.getfile(incmd.dagcmd.__class__)

		if incmd is not None:
			self.lineno = inspect.findsource(incmd.dagcmd.fn)[1] + 1#-> Line Number

		dag.config.DEFAULT_EDITOR.open_file(self.filepath, self.lineno)


	def process_ic_response(self, ic_response):
		ic_response.append_response(f"File opened in Sublime: <c u b>{self.filepath}:{self.lineno}</c>")


@directive("baseurl", "b")
class Directive_Baseurl(DagDirectiveDontRun):
	def __init__(self):
		self.baseurl = ""


	def preprocess_incmd(self, incmd):
		dagcmd = incmd.dagcmds[-1]
		self.baseurl = dagcmd.settings.baseurl or f"No base URL detected for module: <c b>{dagcmd.name}</c>"

	def process_ic_response(self, ic_response):
		ic_response.append_response(self.baseurl)


@directive("choices", "c")
class Directive_Choices(DagDirective):
	def preprocess_incmd(self, incmd):
		pass

	def process_ic_response(self, ic_response):
		try:
			choices = ic_response.raw_response.choices() or "None"
			ic_response.append_response(f"\n\n<c bold>Choices/Labels:</c>{choices}")
		except (AttributeError, TypeError) as e:
			ic_response.append_response(f"\n\n<c bold>Cannot get labels for response: {e}</c>")


@directive("size", "s")
class Directive_Size(DagDirective):
	def preprocess_incmd(self, incmd):
		pass

	def process_ic_response(self, ic_response):
		try:
			ic_response.append_response(f"\n\n<c bold>Size:</c>{len(ic_response.raw_response)}")
		except (AttributeError, TypeError) as e:
			ic_response.append_response(f"\n\n<c bold>Cannot get response's size: {e}</c>")


@directive("keys", "k")
class Directive_Size(DagDirective):
	def preprocess_incmd(self, incmd):
		pass

	def process_ic_response(self, ic_response):
		try:
			ic_response.append_response(f"\n\n<c bold>Keys:</c>{[k for k in ic_response.raw_response.keys()]}")
		except AttributeError:
			ic_response.append_response(f"\n\n<c bold>Cannot get response's keys.</c>")


@directive("debug", "D")
class Directive_Debug(DagDirective):
	def __init__(self):
		self.oldvalue = None

	def preprocess_incmd(self, incmd):
		breakpoint()
		self.oldvalue = dagdebug.DEBUG_MODE
		dagdebug.DEBUG_MODE = True
		print(f"DagCmd Debug Mode: {dagdebug.DEBUG_MODE}")

	def process_ic_response(self, ic_response):
		dagdebug.DEBUG_MODE = self.oldvalue


@directive("doc", "d")
class Directive_Documentation(DagDirectiveDontRun):
	def preprocess_incmd(self, incmd):
		dag.launch(incmd.settings.doc)

	def process_ic_response(self, ic_response):
		pass




@directive("test", "T")
class Test(DagDirective):
	def preprocess_incmd(self, incmd):
		breakpoint()
		return


	def process_ic_response(self, ic_response):
		breakpoint()
		pass