import dag


@dag.arg.Int("--count", max = 25)
@dag.cmd
def guineapig(color: dag.Color = "#EF689C", count = 1):
	"""A useful method for generating guinea pigs"""

	response = ""

	for i in range(count):
		response += color.ctag("  q ----- p \n  | '   ' |  \n  |   v   |\n  \   ^   /\n\n")

	return response