import re, contextlib
from typing import Mapping

import dag
from dag.parser import arguments, inputscripts, dagargparser, incmds


LHMAP = {
		"a": ";",
		"s": "l",
		"d": "kl",
		"f": "j,",
		"g": "hjin",
		"h": "h", # This is here bc sometimes I type h with my left hand
		"q": "p",
		"w": "oye",
		"e": "iu",
		"r": "uyi",
		"t": "yur", # Some left-hand letters are in the value because typing "ur" sometimes makes me "rt" when I mean "rr"
		"z": "/m",
		"x": ".",
		"c": ",",
		"v": "mngb",
		"b": "nm",
		"1": "-",
		"2": "0",
		"3": "9",
		"4": "8",
		"5": "7",
		"6": "6",
	}



def create_character_separated_regex(text):
	return ".*" + ".*".join(list(text)) + ".*"


def dag_complete_beginning(completion_list: list[str], text: str) -> list[str]:
	return sorted([item for item in completion_list if item.startswith(text)])


def dag_complete_contains(completion_list: list[str], text: str) -> list[str]:
	return sorted([item for item in completion_list if text in item])



def dag_complete_regex_contains(completion_list: list[str], text: str) -> list[str]:
	if "*" in text:
		return completion_list

	regexstr = create_character_separated_regex(text)
	return sorted([item for item in completion_list if re.search(regexstr, item)])


def generate_searchstr_from_word(word: str) -> str:
	searchstr = ".*"

	for ch in word:
		searchstr += "[" + "|".join(ch + LHMAP.get(ch, "")) + "].*"

	return searchstr



def dag_complete_lefthand_fuzzy(completion_list: list[str], text: str) -> list[str]:
	# Currently capping text length at 10 because time to do this blows up exponentially with length

	# Search string. Will turn into something like ".*[f|j].*[a|;].*[v|n|m].*" for regex searching
	searchstr = generate_searchstr_from_word(text)
	return sorted([c for c in completion_list if re.search(searchstr, c)], key = len)



def fuzzier_complete_lefthand_fuzzy(completion_list: list[str], text: str) -> list[str]:
	searchstr = generate_searchstr_from_word(text)
	splitsearchstr = searchstr.split(".*")

	items = []

	for i in range(1, len(splitsearchstr)-1): # Range from 1..#splitsearchstr-1 bc not removing first or last ".*" for any searches
		isplitsearchstr = splitsearchstr[:i] + splitsearchstr[i+1:]
		isearchstr = ".*".join(isplitsearchstr)

		items += [c for c in completion_list if re.search(isearchstr, c)]

	dag.bb.completetest()

	return sorted(set(items), key=len)



def get_completion_incmd(line: str):
	with dag.ctx("completer_active", "skip_validate_inputarg", "skip_type_parser", "parse_while_valid", "skip_breakpoint", "complain_breakpoint_skip"):
		incmd = inputscripts.generate_from_text(line).get_last_incmd()

		if not incmd.raw_parsed and incmd.tokens:
			incmd.tokens = incmd.tokens[:-1]
			incmd.initialize()

		return incmd



def complete_line(line: str) -> list[str]:
	with dag.ctx("completer_active", "skip_validate_inputarg", "skip_type_parser"):
		with dag.ctx("parse_while_valid"):
			incmd = get_completion_incmd(line)

		word = "" if not line or line.endswith(" ") else line.split()[-1]
		return complete_completion_incmd(incmd, word)



def complete_completion_incmd(incmd, word: str) -> list[str]:
	with dag.ctx(active_incmd = incmd, active_dagcmd = incmd.dagcmd):
		# Pop the last-parsed item because it doesn't currently need to be typeparsed for completion to work

		if word and incmd.raw_parsed:
			incmd.raw_parsed.popitem()
			pass

		# Running the parser is what enables dynamically-changing tab-completion choices
		with dag.ctx(parse_while_valid = True):
			typedparser = dagargparser.TypedParser(incmd)
			parsed = typedparser.parse()

		pincmd = incmds.ParsedInputCommand(incmd, parsed)

		return pincmd.complete(word)


def dag_complete(word, candidates):
	completion_list = [dag.strtools.escape_unescaped_spaces(c, ignore_trailing_space = True) for c in set(candidates)] # remove duplciates and turn "wow ok" -> "wow\ ok"

	items = []

	# IF "*" already in word, it's not being used for completion, so just return items. (this is so that "git add *" doesn't complain about repeated *'s)
	if "*" in word:
		return items

	items = dag_complete_beginning(completion_list, word)

	# IF we have optionso that complete from beginning: Return those results
	if items:
		return items

	# IF not items: Look for any matches that fit .*c.*h.*a.*r.* pattern and starts with word start char
	if len(items) < 10:
		items = dag_complete_regex_contains(completion_list, word)
		items = [i for i in items if i[0] == word[0]]
		items += sorted(items, key=len)

	#if not items and all(w in LHMAP for w in word): -> removed because lhfuzzy also turns "ompl" into "completeline"
	if len(items) < 10:	
		items = dag_complete_lefthand_fuzzy(completion_list, word)
		sizeitems = [i for i in items if len(i) == len(word)]
		items += sizeitems or items

	if not items:
		items += fuzzier_complete_lefthand_fuzzy(completion_list, word)
		pass


	return list(dict.fromkeys(items))


#>>>> InputCommand Completer
class InputCommandCompleter:
	def __init__(self, pincmd):
		self.pincmd = pincmd


	def complete(self, word: str, parsed: Mapping) -> list[str]:
		completion_list, word = self.get_completion_candidates(word, parsed)
		return dag_complete(word, completion_list)


	def get_completion_candidates(self, word: str, parsed: Mapping) -> tuple[list[str], str]:
		completion_list = []
		inputarg = None

		if self.pincmd.inputargs:
			inputarg = self.pincmd.inputargs[-1]

		# IF arg is a prefixed arg: Handle completion of name or value
		if isinstance(inputarg, arguments.PrefixedCliArgument):
			strippedtext = word.removeprefix(inputarg.prefix)
			completion_list = inputarg.get_completion_candidates(strippedtext, self.pincmd, parsed) # Note, prefixes are supplied by inputargs for cases like "filts" where the value doesn't have a prefix
			return completion_list, word

		# ELSE, not a prefixed arg: Complete positional DagArg
		else:
			# Return completion candidates for current arg
			if self.pincmd.dagcmd:
				items, word = self.complete_dagarg_from_incmd(word, parsed)
				completion_list += items

			# Return list of dagcmd names if on first argument
			if len(self.pincmd.argtokens) <= 1:
				completion_list += [n for n in self.pincmd.dagcmd.get_dagcmd_names()]

				if self.pincmd.is_default_cmd:
					completion_list += [n for n in self.pincmd.dagcmd.dagapp.get_dagcmd_names()]
			
		return completion_list, word


	def complete_dagarg_from_incmd(self, word: str, parsed: Mapping) -> tuple[list[str], str]:
		items = []
		dagcmd = self.pincmd.dagcmd

		with dag.ctx(active_dagcmd = dagcmd, parsed = parsed):
			try:
				# completes with function names if we are completing arg name
				if self.pincmd.is_current_long_argname:
					word = self.pincmd.active_argtext
					items = [dagarg.name for dagarg in self.pincmd.dagargs.namedargs.values()]
				# Else, assume is a DagArg: Complete DagArg
				else:
					inputdagarg = self.pincmd.active_inputdagarg

					if inputdagarg:
						items, word = inputdagarg.generate_completion_list(self.pincmd, word, parsed)

					# If there are subcmds, get the dagcmd names
					if dagcmd and isinstance(dagcmd, dag.DagCmd) and len(self.pincmd.args) <= 1:		#one or fewer args indicates may be typing subcmd name
						items.extend([name for name in dagcmd.dagcmds.names()])

			except Exception as e:
				breakpoint()
				dag.echo(f"Completion Error: <c b>{e}</c>")

		return items, word
#<<<< InputCommand Completer