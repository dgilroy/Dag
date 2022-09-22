import dag
from dag.exceptions import DagArgParserError
from dag.parser.InputDagArg import InputDagArg



# This is used so that "argval" knows whether its contents were filled from parsed or not
class UnfilledArg:
	pass


# parse_known will parse while possible, and once it hits something that doesn't work (like an invalid choice), return successfully parsed objects
def get_typed_parsed(incmd, parse_while_valid = False):
	typed_parsed = {}

	with dag.ctx(active_dagcmd = incmd.dagcmd, parsed = typed_parsed):
		parsed = incmd.raw_parsed
		raw_parsed = {k: " ".join(v) for k, v in parsed.items()}
		

		for dagarg in incmd.dagargs:
			argname = dagarg.clean_name
			target_name = dagarg.settings.target
			argval = UnfilledArg
			try:
				inputarg = incmd.inputargs.get(argname, None) or InputDagArg(incmd, dagarg = dagarg)
			except TypeError as e:
				breakpoint()
				pass

			incmd.parser_args.append(inputarg)

			# If raw_value of dagarg was parsed into incmd
			if inputarg.name in parsed:
				if "flag" in inputarg.settings:
					argval = inputarg.settings.flag
				elif inputarg.is_do_nargs_join_before_type() and isinstance(inputarg.settings.get("nargs_join"), str):
					argval = inputarg.settings.nargs_join.join(parsed.get(inputarg.name))
				else:
					argval = parsed.get(inputarg.name)

				# Argval was never actually entered (may have just been a space), so continue onward
				if argval == [""]:
					argval = UnfilledArg

			# If argval had no value in parsed
			if argval == UnfilledArg:
				# Skip unfilled Resource dagarg for Collecitons
				if inputarg.skip_if_unfilled():
					continue

				# Prompt value
				if inputarg.is_do_prompt():
					argval = inputarg.prompt_value()
				# Check default values
				else:
					try:
						argval = inputarg.default_value()
					except (AttributeError, ValueError, KeyError) as e:
						# If dagarg is required: Either return what we've gathered so far, or raise an error
						if inputarg.settings.required:
							if parse_while_valid:
								return typed_parsed

							breakpoint()
							raise DagArgParserError(f"Argument parser error: Please enter value for required dagarg: {inputarg.name}")
						# Else, dagarg isn't required: Stop processing dagarg and move on to next dagarg
						else:
							continue


			# Some argvals may not be str if the function's default value isn't a str
			if isinstance(argval, str):
				# If the value is not in dagarg's "choices": raise DagArgParserError 
				if inputarg.settings.get("choices") and argval not in (choices := inputarg.settings.choices):
					if parse_while_valid:
						return typed_parsed

					raise DagArgParserError(f"Argument parser error: Argument <c bold black bg-red>{inputarg.name}</c> cannot take value <c bold>\"{argval}\"</c>\n\nPlease choose from <c bold>[{', '.join(choices)}]</c>")

				# If a type is defined for dagarg, process the type
				argval = inputarg.parse_parser_value(argval)

				if isinstance(argval, str) and not inputarg.settings.raw:
					argval = inputarg.process_string_value(argval)

					# Prefix/Suffix/Wraps
					# Don't use removesuffix/removeprefix without checking that the string actually starts with said stuff
					## PREFIX
					if inputarg.settings.get("prefix") and (prefix := str(inputarg.settings.prefix)):
						argval = prefix + str(argval) if not str(argval).startswith(prefix) else str(argval)
					
					## SUFFIX
					if inputarg.settings.get("suffix") and (suffix := str(inputarg.settings.suffix)):
						argval = str(argval) + suffix if not str(argval).endswith(suffix) else str(argval)
						
					## WRAPS
					if inputarg.settings.get("wrap") and (wrap := str(inputarg.settings.wrap)):
						argval = wrap + str(argval) if not str(argval).startswith(wrap) else str(argval)
						argval = str(argval) + wrap if not str(argval).endswith(wrap) else str(argval)


			if not inputarg.is_do_nargs_join_before_type() and isinstance(inputarg.settings.get("nargs_join"), str) and isinstance(argval, (list, tuple)):
				argval = inputarg.settings.nargs_join.join(argval)
				
			typed_parsed[target_name or argname] = argval

		return typed_parsed


