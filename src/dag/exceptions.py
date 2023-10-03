import traceback, sys
from contextlib import contextmanager

import dag

class DagError(Exception):	pass

class DagExitDagCmd(Exception):	pass

class DagParserError(DagError): pass

class DagArgParserError(DagParserError): pass


class DagSubprocessRunError(DagError): pass


# Gets raised when the command is invalid
class DagInvalidCommandException(DagError):	pass


# Gets raised when the command is invalid
class DagArgValidationException(DagError): 
	def __init__(self, message):
		# Call the base class constructor with the parameters it needs
		super().__init__(f"<c greenyellow u>Dag Validation Error:</c greenyellow u> {message}")


		
# Empty error so argument "catch" default setting wont complain 
class DagPlaceholderError(Exception):	pass

		
# Gets raised when "false" is called in CLI
class DagFalseException(Exception): pass

# Used to indicate reloading
class DagReloadException(Exception): pass

# If more than one CommaList is in InputCommand, raise exception
class DagMultipleCommaListException(Exception): pass

# Used to break loops from within functions
class DagContinueLoopException(Exception): pass

# Used to break loops from within functions
class DagBreakLoopException(Exception): pass

class StopDagCmdExecutionException(Exception): pass




class ExcCatcher:
	def __init__(self):
		self.exc = None

	@property
	def tb(self):
		if self.exc:
			print_traceback(self.exc)

	def __repr__(self):
		rep = dag.format(f"<c #444>{object.__repr__(self)}</c>")
		if self.exc:
			self.tb

		return rep


@contextmanager
def catch(*errtypes):
	errtypes = errtypes or Exception
	
	exccatcher = ExcCatcher()

	try:
		yield exccatcher
	except errtypes as e:
		exccatcher.exc = e
		print_traceback(e)
		dag.echo("<c b red><<< Exception caught:</c b red>")
		breakpoint(framesback = 2)
		pass



@contextmanager
def postmortem(*errtypes):
	try:
		yield
	except BaseException as e:
		dag.debug.postmortem(e)



@contextmanager
def passexc(*errtypes):
	errtypes = errtypes or Exception
	
	try:
		yield
	except errtypes as e:
		pass


def print_traceback(exc = None, **kwargs):
	if not (dag.ctx.silent or dag.settings.silent):
		if exc is None:
			traceback.print_exc(**kwargs)
		else:
			traceback.print_exception(exc, **kwargs)