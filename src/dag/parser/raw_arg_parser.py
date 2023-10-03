import dag
from dag.parser import arguments


class RawArgParser:
	def __init__(self, incmd, default_argclass):
		self.incmd = incmd
		self.tokens: list[str] = incmd.argtokens[:]
		self.proctokens: list[str] = self.tokens[:]

		self.ignored_prefixes: list[str] = []
		self.default_argclass = default_argclass


	def parse_args(self) -> None:
		# IF the previous inputcommand piped its response: Insert
		if dag.ctx.piped_responses:
			insertidx = 0 if not self.incmd.dagcmd.is_regexcmd else 1
			self.proctokens.insert(insertidx, "$_DAG_PIPED_VALUE_0")

		# WHILE there are tokens to consume: turn tokens into parsed arguments
		while self.proctokens:
			tokens = self.proctokens[:] # A copy of proctokens to check later whether or not anything has been done to them
			argclass = self.default_argclass # Default arg type is InputDagArg. Currently, this won't change unless a prefixed arg is detected (e.g. =u, ##filt, etc...)

			# IF incmd isn't raw, the argument is a prefixed arg, and the prefix isnt currently disabled: Process the arg
			if not self.incmd.settings.raw and (prefix := arguments.get_arg_prefix_greedy(self.proctokens[0])) and prefix not in self.ignored_prefixes:
				argclass = arguments.registered_prefixes[prefix]

				# IF the prefixed arg is valid (e.g: - is only a valid prefix if followed by a letter): Process the arg
				if argclass.is_valid_prefixed_arg(self.proctokens[0]): 
					# IF the token is only the prefix and the prefix should be ignored when such a token is given: Ignore the token
					if prefix == self.proctokens[0] and argclass.is_start_ignore_when_empty: # len is there so things like ">/copy" don't get ignoredd
						self.ignored_prefixes.append(self.proctokens.pop(0))
						continue
				# ELSE, prefixed arg isn't valid (e.g.: -30 is not a valid shortdagarg): Revert to positional dagarg
				else:
					argclass = self.default_argclass

			# FOR each arg in the token (e.g.: "=ur" yields both "==update" and "==raw"): Process the arg
			for arg in argclass.yield_args(self):
				arg.parse(self)
				inputarg = arg.generate_input_argument(self)
				self.incmd.add_inputarg(inputarg)

			# IF tokens haven't been modified above: Assume error and break. Otherwise PromptToolkit will randomly hang 
			if tokens == self.proctokens:
				self.proctokens.pop(0)