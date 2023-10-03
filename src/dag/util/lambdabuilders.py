import dag
from dag.lib import comparison
from dag.util.attribute_processors import AttrCallframeRecorder



#>>>> LambdaBuilder
class LambdaBuilder(AttrCallframeRecorder):
	def _do_call(self, root = None):
		with dag.ctx(active_lambdabuilder_root = root):
			if root:
				item = root
				for record in self._stored_attrs or []:
					if record.attr_name == "RSEARCH" and record.args:
						item = re.search(record.args[0], item) #record.args[0] is the regex pattern to search for
					if record.attr_name == "LEN":
						item = len(item)
					elif record.attr_name == "INT":
						item = int(item)
						continue
					elif record.attr_name == "STR":
						item = str(item)
						continue
					elif record.attr_name == "DTIME":
						item = dag.DTime(item)
						continue
					elif record.attr_name == "TYPE" and record.args:
						item = record.args[0](item)
						continue

					item = record.get_item(item)

				return item
#<<<< LambdaBuilder



def convert_lb_to_string(lb: LambdaBuilder, is_root_call: bool = True) -> str:
	def make_str(text):
		if isinstance(text, str):
			return f"\"{text}\""

		return str(text)
		

	if not isinstance(lb, LambdaBuilder):
		return make_str(lb)

	strrep = "" if is_root_call else "r_"

	for attr in lb._stored_attrs:
		attrname = attr.attr_name

		match attrname:
			case "__getitem__":
				strrep += "[" + ":".join([convert_lb_to_string(x, is_root_call = False) for x in attr.args]) + "]"
				breakpoint(show = strrep)
				pass
			case "__call__":
				strrep += "("
				breakpoint(show = strrep)
				pass
			case _ if attrname in comparison.DUNDEROPS:
				strrep += f" {comparison.DUNDEROPS[attrname]} " + " ".join([convert_lb_to_string(x, is_root_call = False) for x in attr.args])
				breakpoint(show = strrep)
				pass
			case _:
				strrep += "."
				strrep += attrname

				if attr.is_called:
					strrep += "(" + ", ".join([convert_lb_to_string(x, is_root_call = False) for x in attr.args]) + ")"

					breakpoint(show = strrep)
					pass


	return strrep