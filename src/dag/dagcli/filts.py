import re, ast
from typing import NoReturn
from functools import partial

import dag
from dag import dagcmds
from dag.lib import comparison
from dag.util import drill
from dag.parser import arguments
from dag.parser.arguments import PrefixedCliArgument
from dag.exceptions import DagParserError



class FiltArg(PrefixedCliArgument, prefix = "##"):
	name = None
	operator = ""
	value = None
	is_start_ignore_when_empty = True


	def do_parse(self, parser) -> None:
		token: str = parser.proctokens.pop(0)
		tokens = parser.proctokens

		if tok := token.removeprefix(self.prefix):
			self.name = tok

		while tokens:
			token = tokens[0]

			if token in comparison.ops:
				if self.operator:
					raise DagParserError(f"Multiple comparison operators passed to filt ({self.operator}, {token}). Only one is allowed")

				self.operator = tokens.pop(0)
				continue

			# If token is a prefixed arg: End parsing
			if arguments.get_arg_prefix_greedy(token):
				return

			self.value = tokens.pop(0).replace("\\ ", " ")
			
			break


	def get_completion_candidates(self, text, incmd, parsed):
		if incmd.is_cached_collection:
			collection = incmd.dagcmd()

			if not collection:
				return [] 

			if self.value is not None:
				return collection.get_values_of(self.name)
			
			items = drill.drill_for_properties(collection[0], drillbits = text, approved_initial_properties = [*collection[0]._response._data.keys()], lstrip = ".")

			return [self.prefix + c for c in items]

		return []


	def filter_icresponse(self, icresponse):
		if self.value is None:
			self.do_partition(icresponse)
		else:
			self.do_filter(icresponse)


	def do_partition(self, icresponse):
		icresponse.raw_response = icresponse.raw_response.partition(self.name)


	def do_filter(self, icresponse):
		def filterfn(value, resource):
			drilledvalue = drill.drill(resource, self.name)

			try:
				return drilledvalue._dag_filt_value(op, value)
			except:
				return op(drilledvalue, value)

		collection = icresponse.raw_response
		opsign = self.operator or "=="
		val = self.value

		if opsign == "=":
			opsign = "=="

		items = collection.create_subcollection()

		op = comparison.ops[opsign]

		val = val[1:] if val and val[0] in ["'", '"'] else val # Strip quotes
		val = val[:-1] if val and val[-1] in ["'", '"'] else val # Strip quotes

		if not dag.rslashes.item_is_rslash(val) and "*" in val:
			val = f"r/^{val}$/".replace("*", ".*")

		# IF val is setup like r/text/: Parse val is regex string and do regex search
		if dag.rslashes.item_is_rslash(val):
			val, flagchars = dag.rslashes.get_regex_content(val)
			flags = dag.rslashes.parse_flagchars(flagchars)

			op = lambda x: re.search(str(val), str(drill.drill(x, self.name)), flags)
			items += collection.filter(op)
		# ELSE val is not regex: search for literal value
		else:
			origval = val
			try:
				val = ast.literal_eval(val)
			except:
				pass
				
			items += collection.filter(partial(filterfn, val))

			# IF val and origval differ: Then val is no longer a string. Search for the string version as well
			# (This is done so that 1967 will match both int 1967 and string "1967")
			if val != origval:
				items += collection.filter(partial(filterfn, origval))

		items.remove_duplicates()
		icresponse.raw_response = items