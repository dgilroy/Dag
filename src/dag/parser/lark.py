import lark

import dag

parser = lark.Lark(r"""
	command_list: command COMMAND_TERMINATOR* command_list*

	command: arg+

	arg: DIGIT+ | WORD | ESCAPED_STRING | comma_list | range

	comma_list: (DIGIT+ | WORD) "," ((DIGIT+ | WORD) | comma_list)

	range: range_inclusive | range_exclusive
	range_exclusive: (DIGIT+ | WORD) "..." (DIGIT+ | WORD)
	range_inclusive: (DIGIT+ | WORD) ".." (DIGIT+ | WORD)


	COMMAND_TERMINATOR: "\\n" | ";" | "|" | "&&" | "||"

	_STRING_INNER: /.*?/
	_STRING_ESC_INNER: _STRING_INNER /(?<!\\)(\\\\)*?/
	ESCAPED_STRING : "\"" _STRING_ESC_INNER "\"" | "'" _STRING_ESC_INNER "'"

	%import common.WORD
	%import common.DIGIT
    %import common.WS
    %ignore WS
""", start = 'command_list')


def test_lark(text = "wow; dog && cat", dodebug: bool = False):
	with dag.catch(lark.exceptions.UnexpectedCharacters, lark.exceptions.UnexpectedEOF) as e:
		return parser.parse(text)