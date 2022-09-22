from contextlib import contextmanager

class DagError(BaseException):	pass


class DagArgParserError(DagError): pass


class DagSubprocessRunError(DagError): pass


# Gets raised when the command is invalid
class DagInvalidCommandException(DagError):	pass


# Gets raised when the command is invalid
class DagArgValidationException(DagError): 
	def __init__(self, message):
		# Call the base class constructor with the parameters it needs
		super().__init__(f"<c greenyellow u>Dag Validation Error:</c greenyellow u> {message}")


		
# Empty error so argument "catch" default setting wont complain 
class DagPlaceholderError(BaseException):	pass

		
# Gets raised when "false" is called in CLI
class DagFalseException(BaseException): pass

# Used to indicate reloading
class DagReloadException(BaseException): pass

# If more than one CommaList is in InputCommand, raise exception
class DagMultipleCommaListException(BaseException): pass

# Used to break loops from within functions
class DagContinueLoopException(BaseException): pass




@contextmanager
def catch(*errtypes):
	errtypes = errtypes or Exception
	
	try:
		yield
	except errtypes as e:
		breakpoint()
		pass