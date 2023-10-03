import ast, types
from enum import Enum

import dag
from dag.lib import mathtools
from dag.exceptions import DagArgParserError
from dag.parser import inputscripts


Sources = dag.enum.Sources("CLI", "PROMPT", "DEFAULT", "PIPE")



class TypedParser:
	def __init__(self, incmd):
		self.incmd = incmd
		self.raw_parsed = incmd.raw_parsed
		self.processed_raw_parsed = incmd.raw_parsed.copy()
		self.typed_parsed = {}
		self.dagargs = {d.clean_name: d for d in self.incmd.dagargs}


	def evaluate_tokens(self, inputarg):
		# Turns "3" into 3, or "[1,2,3]" into a list, etc
		rp = self.processed_raw_parsed.get(inputarg.target)

		for i, rawvalue in enumerate(rp or ()):
			if not isinstance(rawvalue, str):
				continue

			if rawvalue == "$_DAG_PIPED_VALUE_0":
				rp[i] = dag.ctx.piped_responses.pop()
				inputarg.src = Sources.PIPE
			elif isinstance(rawvalue, dag.Nabber):
				rp[i] = rawvalue._nab()
			elif dag.strtools.text_is_wrapped_with_unescaped(rawvalue, "(", ")"):
				with dag.instance.subinstance():
					rp[i] = inputscripts.generate_from_text(rawvalue[1:-1]).execute().raw_response
			elif dag.strtools.text_is_wrapped_with_unescaped(rawvalue, "{", "}") or dag.strtools.text_is_wrapped_with_unescaped(rawvalue, "[", "]"):
				# If this is a slice (e.g. [1:3], [:2], etc), then ignore (used by drill dagcmd)
				if dag.strtools.text_is_wrapped_with_unescaped(rawvalue, "[", "]") and ":" in rawvalue:
					pass
				else:
					rp[i] = ast.literal_eval(rawvalue)


	def evaluate_via_prompt(self, inputarg):
		while True:
			promptid = "dagargparser-prompt_" + inputarg.incmd.dagcmd.cmdpath("-") + "_" + inputarg.name
			
			argval = inputarg.prompt_value(self.typed_parsed, id = promptid)
			inputarg.src = Sources.PROMPT

			if argval == "" and inputarg.settings.required:
				dag.echo("<c red / Must enter value>")
				continue
			break

		return argval


	def evaluate_default_value(self, inputarg):
		try:
			argval = [inputarg.default_value(self.incmd)]
			inputarg.src = Sources.DEFAULT
			return argval
		except (AttributeError, ValueError, KeyError) as e:
			# If dagarg is required: Either return what we've gathered so far, or raise an error
			if inputarg.settings.required:
				if dag.ctx.parse_while_valid:
					raise dag.BreakLoopException()

				raise DagArgParserError(f"Argument parser error: Please enter value for required dagarg: {inputarg.name}") from e
			# Else, dagarg isn't required: Stop processing dagarg and move on to next dagarg
			else:
				raise dag.ContinueLoopException()


	def handle_str_wrapping(self, inputarg, argval):
		# Prefix/Suffix/Wraps
		# Don't use removesuffix/removeprefix without checking that the string actually starts with said stuff
		# Done this way so "None" doesn't get turned into a string

		if inputarg.settings.get("prefix") and (prefix := str(inputarg.settings.prefix)):
			argval = prefix + str(argval) if not str(argval).startswith(prefix) else str(argval)
		
		## SUFFIX
		if inputarg.settings.get("suffix") and (suffix := str(inputarg.settings.suffix)):
			argval = str(argval) + suffix if not str(argval).endswith(suffix) else str(argval)
			
		## WRAPS
		if inputarg.settings.get("wrap") and (wrap := str(inputarg.settings.wrap)):
			argval = wrap + str(argval) if not str(argval).startswith(wrap) else str(argval)
			argval = str(argval) + wrap if not str(argval).endswith(wrap) else str(argval)

		return argval


	def process_str_value(self, inputarg, argval):
		# If the value is not in dagarg's "choices": raise DagArgParserError 
		if inputarg.settings.get("choices") and argval not in (choices := inputarg.settings.choices):
			if dag.ctx.parse_while_valid:
				raise dag.BreakLoopException()

			raise DagArgParserError(f"Argument parser error: Argument <c bold black bg-red>{inputarg.name}</c> cannot take value <c bold>\"{argval}\"</c>\n\nPlease choose from <c bold>[{', '.join(choices)}]</c>")

		if isinstance(argval, str):
			try:
				default = inputarg.default_value(self.incmd)

				# If default is UnfilledArg: Pass, don't cast its type
				if default is dag.UnfilledArg:
					pass
				elif not isinstance(default, str):
					try:
						argval = type(default)(argval)
					except Exception:
						pass
			except Exception:
				pass

		argval = self.handle_str_wrapping(inputarg, argval)

		return argval


	def get_argval_if_not_in_raw_parsed(self, inputarg):
		# Skip unfilled Resource dagarg for Collecitons
		if inputarg.skip_if_unfilled():
			raise dag.ContinueLoopException()

		# if inputarg should be prompted: Prompt value
		if inputarg.is_do_prompt() and not dag.ctx.parse_while_valid:
			argval = self.evaluate_via_prompt(inputarg)
		# Else, inputarg isn't meant to be prompted: Check default values
		else:	
			argval = self.evaluate_default_value(inputarg)

		self.processed_raw_parsed[inputarg.target] = dag.listify(argval)		

		return argval


	def evaluate_flag_value(self, inputarg, dagarg):
		if dagarg.settings.negatable and inputarg.rawvalue and inputarg.rawvalue[0].startswith("--no-"):
			return [not inputarg.settings.flag]

		return [inputarg.settings.flag]


	def evaluate_argval(self, inputarg):
		argval = self.processed_raw_parsed.get(inputarg.target)

		# If arg uses nargs_join: Join the words together via nargs join
		if isinstance(inputarg.settings.get("nargs_join"), str):
			try:
				argval = [inputarg.settings.nargs_join.join(argval)]
			# TypeError implies argval might not be strings, so ignore. (e.g. editor item's default is None)
			except TypeError:
				pass

		return argval

	def maybe_extract_from_list(self, inputarg, argval):
		if len(argval) == 1 and (inputarg.settings.get("nargs", 1) == 1 or "nargs_join" in inputarg.settings or "flag" in inputarg.settings):
			return argval[0]

		return argval


	def apply_arg_type(self, inputarg, argval):
		# If inputarg came from PIPE: Don't process further
		# This was implemented so that "which nhl | e" works. otherwise "which nhl" was turned into "FILEPATH/TO/NHL.py:LINE-NO" and then incorrectly turned into an inputcmd
		if inputarg.src is Sources.PIPE:
			return self.maybe_extract_from_list(inputarg, argval)

		argtype = inputarg.argtype(self.incmd)
		argval = [inputarg.process_raw_argval(val, self.incmd) if isinstance(val, str) else val for val in argval]
		
		# If no argtype is set: Don't process further, but possibly take it out of its list object 
		if argtype is None:
			return self.maybe_extract_from_list(inputarg, argval)

		metadata = ()

		# If annotated alias: Extract the true argtype as well as any metadata (e.g. list[int] -> argtype = list; metadata = int)
		if isinstance(argtype, types.GenericAlias):
			metadata = dag.get_annotated_metadata(argtype)
			argtype = dag.get_annotated_class(argtype)

		for i in range(len(argval)):
			if isinstance(argval[i], argtype):
				continue

			# Bool is here so that None becomes "False"
			if argtype is bool:
				try:
					argval[i] = bool(ast.literal_eval(argval[i]))
				except ValueError:
					pass

			elif argval[i] is not None:
				try:
					# If argtype is int or float: evaluate math expression, (e.g. so 2*3 becomes 6)
					if argtype in (int, float):
						argval[i] = argtype(mathtools.eval_math(argval[i]))
					# Elif argtype is list with metadata (e.g. list[int]): Cast argval to the metadata type
					elif argtype == list and metadata:
						argval[i] = metadata[0](argval[i])
					# Elif argtype is tuple with metadata: Cast argvalue to appropriate type from metadata
					elif argtype == tuple and metadata:
						# If tuple has 2 args and the 2nd one is ... (e.g. tuple[int, ...]): All the tuple's elements are the 1st metadata entry
						if len(metadata) == 2 and metadata[1] == ...:
							argtypei = metadata[0]
						# Else, tuple does not have ... as metadata (e.g. tuple[int,str]): The type of the arg matches the ith entry in the metadata
						else:
							argtypei = metadata[i]

						argval[i] = argtypei(argval[i])
					else:
						argval[i] = argtype(argval[i])
						
				except (ValueError, TypeError) as e:
					raise e

		# IF argtype is list or tuple: Cast response as list or tuple
		if argtype in (list, tuple):
			argval = argtype(argval)
		# ELSE, type isn't explicitly a list: Maybe extract value from list if right criteria is met
		else: 
			argval = self.maybe_extract_from_list(inputarg, argval)

		return argval


	def parse(self):
		from dag.parser.inputdagargs import InputDagArg
		
		with dag.ctx(active_dagcmd = self.incmd.dagcmd, raw_parsed = self.raw_parsed, parsed = self.typed_parsed):
			for dagarg in self.dagargs.values():
				# Try for break/continue exceptions
				try:
					inputarg = self.incmd.inputdagargs.get(dagarg.target, None) or InputDagArg(dagarg, self.incmd)
					argval = dag.UnfilledArg

					#If arg was not submitted into CLI: Evaluate its value by other means
					if inputarg.target not in self.processed_raw_parsed:
						argval = self.get_argval_if_not_in_raw_parsed(inputarg)
					# ELSE, value was input via CLI: Process the value
					elif not inputarg.src:
						inputarg.src = Sources.CLI

					# Evaluates piped value, or turns "[1,2,3]" into a literal list, etc
					self.evaluate_tokens(inputarg)

					# If inputarg is a flag: Evaluate flag value
					if "flag" in inputarg.settings:
						if inputarg.src is not Sources.DEFAULT:
							argval = self.evaluate_flag_value(inputarg, dagarg)
						else:
							pass
					# ELSE, inputarg is not flag: Get its value 
					else:
						argval = self.evaluate_argval(inputarg)

					argval = dag.listify(argval) # Need argval to be in list to properly process nargs

					# If input came from CLI: Process input, including possibly stripping quotes around strings 
					# This is done *after* evaluating so that "[1,2,3]" isn't stripped and then turned into a list literal
					with dag.catch() as e:
						for i, val in enumerate(argval):
							if isinstance(val, str):
								if inputarg.src == Sources.CLI:
									argval[i] = inputarg.process_cli_value(val)

					# If a type is defined for dagarg, process the type
					argval = self.apply_arg_type(inputarg, argval)

					# Some argvals may not be str if the function's default value isn't a str
					if isinstance(argval, str) and not inputarg.settings.raw:
						argval = self.process_str_value(inputarg, argval)
					elif isinstance(argval, dag.Nabber):
						breakpoint() #### Not sure if I need this elif branch
						argval = rawargval._nab()
						
					argval = inputarg.process_parsed_argval(argval)
					
					self.typed_parsed = inputarg.apply_value_to_parsed(argval, self.typed_parsed)
				except dag.ContinueLoopException:
					continue
				except dag.BreakLoopException:
					break
				except (Exception, BaseException) as e:
					if dag.ctx.parse_while_valid:
						return self.typed_parsed
					raise e

			return self.typed_parsed