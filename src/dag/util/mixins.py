import json

class DagLaunchable:
	def _dag_launch_item(self):
		return


class DagJsonEncodable:
	def _dag_json_encoder(self):
		return json.JSONEncoder


class CacheFileNamer:
	def _dag_cachefile_name(self):
		return
	

class DagStyleFormattable:
	def _dag_formatter_fn(self):
		return


class DagFiltable:
	def _dag_filt_value(self, other, op):
		return NotImplemented


class DagDrillable:	pass


class DagSettings:
	def _dag_get_settings(self):
		return


class DagDriller:
	def _dag_drill(self, drillee):
		return


class Alistable:
	pass


class DagCompletable:
	def complete(self,incmd):
		pass

	def _dag_modify_completion_text(self, text):
		return text


class DagResourceRepr:
	def _dag_resource_repr(self):
		return self.__repr__()



#@dill.register(abc.ABCMeta)
#def save_abc(pickler, obj):
#	from pickle import _Pickler as StockPickler
#	StockPickler.save_type(pickler, obj)



class CLIInputtable:
	def process_incmd_meta(self, incmd, parsed):
		pass

	def parse_name(self, name: str):
		pass

	def process_parsed_cmd(self):
		pass

	def process_cli_response(self, ic_response):
		pass

	def process_incmd(self, incmd):
		return incmd

	def filter_icresponse(self, icresponse):
		pass

	def process_icresponse(self, ic_response):
		pass

	def process_raw_parser(self, rawparser):
		return True

	def get_completion_candidates(self, text, incmd, parsed):
		return []

	def pre_execute_dagcmd(self, incmd):
		pass

	def post_execute_dagcmd(self, incmd, response):
		pass

	def expand_parsed(self, parsed):
		pass

	def pt_process_completion(self, completion):
		return completion

	def provide_autofill(self, incmd, obj):
		return ""

	def autofill_move_cursor(self, incmd, obj):
		"""
		How much to move cursor after autosuggestion (e.g., autocompelte provides '' and then moves back a space so that cursor is inside the '')
		"""
		return 0