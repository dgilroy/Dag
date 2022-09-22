import dag
from dag import this



@dag.mod("newton", baseurl = "https://newton.now.sh/api/v2/", default_cmd = this.operate, doc = "https://github.com/aunyks/newton-api", response_parser = dag.JSON)
class Newton(dag.DagMod):
	"""Perform some math operations"""

	@dag.arg("value", nargs = -1, nargs_join = "")
	@dag.arg("operation", replace = {"/" : "(over)"}, choices = ["simplify", "factor", "derive", "integrate", "zeroes", "tangent", "area", "cos", "sin", "tan", "arccos", "arcsin", "arctan", "abs", "log"])
	@dag.cmd(display = this._display_operation, cache = True)
	def operate(self, operation, value):
		value = value.replace("/", "(over)")
		return dag.get(f"{operation}/{value}")


	def _display_operation(self, response, formatter):
		formatter.add_row(response.result, style = "bold")