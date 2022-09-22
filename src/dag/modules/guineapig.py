from functools import partial

import dag
from dag import this



@dag.mod("guineapig", default_cmd = this.guinea_pig)
class GuineaPig(dag.DagMod):
	"""A useful method for generating guinea pigs"""

	@dag.arg.Int("--count", max = 25)
	@dag.arg.Color("color", nargs = -1)
	@dag.cmd()
	def guinea_pig(self, color = "#EF689C", count = 1):
		response = ""
		total_colors = len(color)

		count = min(max(len(color), count), 25)

		for i in range(count):
			response += f"<c {color[i % total_colors]}>  q ----- p \n  | '   ' |  \n  |   v   |\n  \   ^   /</c>\n\n"

		return response