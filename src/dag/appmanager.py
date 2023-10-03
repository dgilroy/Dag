import json, importlib, inspect, os, pathlib, sys, copy

import dag
from dag import applications, dagcmds


APPINFO_PATH = dag.directories.STATE / "appinfo"
FILEPATH = "filepath"
LASTMODIFIED = "last-modified"
COLOR_NAME = "color_name"
COLOR = "color"
IS_REGEXCMD = "is_regexcmd"
REGEXCMD_PRIORITY = "regexcmd_priority"


class AppManager:
	def __init__(self):
		self.appinfo = {}
		self.load_appinfo()
		self.initialize_session()


	def initialize_session(self) -> None:
		with dag.ctx(active_appmanager = self):
			self.remove_deleted_pathfiles()
			self.reregister_updated_pathfiles()
			self.check_pathinfo_for_new_files()


	def load_appinfo(self):
		appinfo = {}

		rawappinfo = dag.file.read.RAW(APPINFO_PATH) # RAW bc otherwise might return with DagResponse.JSON during "completeline nhl"
		if not rawappinfo:
			self.appinfo = {}
		else:
			self.appinfo = json.loads(rawappinfo) # RAW bc otherwise might return with DagResponse.JSON during "completeline nhl"

		return self.appinfo



	def clear_appinfo(self):
		APPINFO_PATH.unlink()
		self.load_appinfo()


	def load_module(self, filepath, add_to_sys = True):
		try:
			filepath = pathlib.Path(filepath)

			modulename = filepath.stem
			spec=importlib.util.spec_from_file_location(modulename,filepath)
			module = importlib.util.module_from_spec(spec)
			spec.loader.exec_module(module)

			# IF adding to sys is enabled and the module is part of dag: Add to sys modules
			
			if add_to_sys and dag.CODE_PATH in filepath.parents:
				filepath, codepath = str(filepath), str(dag.CODE_PATH)

				filepath = filepath.removesuffix(".py")
				pathparts = filepath.replace(codepath, "").strip("/").split("/")
				modulename = "dag." + ".".join(pathparts)

				sys.modules[modulename] = module

			return module
		except AttributeError as e:
			breakpoint()
			return False


	def get_regexcmds_info(self):
		return {k:v for k,v in self.appinfo.items() if v.get(IS_REGEXCMD)}



	def load_cmd_module(self, cmdname):
		cmdinfo = self.appinfo.get(cmdname)

		if not cmdinfo:
			if regexcmds_info := self.get_regexcmds_info():
				sorted_regexcmds_info = dict(sorted(regexcmds_info.items(), key=lambda item: item[1][REGEXCMD_PRIORITY]))

				for regexcmdname, regexcmdinfo in sorted_regexcmds_info.items():
					if dag.rslashes.fullmatch_rslash(cmdname, regexcmdname):
						self.load_module(regexcmdinfo[FILEPATH])
						return

			raise ValueError(f"Cmd {cmdname} not found")

		self.load_module(cmdinfo[FILEPATH])


	def process_identifier(self, identifier, updating: bool = False, silent = False):
		names = [identifier.name] + dag.listify(identifier.settings.aka, stripnone = True)
		filepath = identifier._callframeinfo.filepath


		with dag.ctx(silent = silent):
			for name in names:
				if name in self.appinfo and str(self.appinfo[name][FILEPATH]) != str(filepath):
					dag.echo(f"SKIPPING <c ub /{name}>: already registered as a command in <c ub / {self.appinfo[name][FILEPATH]}>")
					continue

				verb, preposition = ("updating", "in") if updating else ("adding", "to")

				dag.echo(f"{verb} <c bu / {identifier.name}> {preposition} app info")

				self.appinfo[name] = {
					FILEPATH: f"{filepath}",
					LASTMODIFIED: os.path.getmtime(filepath),
					COLOR_NAME: identifier.settings.get("color_name", None),
					COLOR: identifier.settings.get("color", None),
					IS_REGEXCMD: identifier.is_regexcmd,
					REGEXCMD_PRIORITY: identifier.settings.regex_priority,
				}


	def process_file(self, filepath: pathlib.Path, updating: bool = False) -> None:
		module = self.load_module(filepath, add_to_sys = False)

		if not module:
			dag.ctags.echo(f"module <c bu>{filepath}</c bu> not valid")


		#for name, item in inspect.getmembers(module):
		#	if (isinstance(item, dagcmds.DagCmd) and item.root == dag.defaultapp) or (isinstance(item, applications.DagApp)):
		#		self.process_identifier(item, updating)


	def register(self, filepath, updating = False):
		if filepath.is_dir():
			for file in filepath.iterdir():
				if file.name.startswith("__"):
					continue
				self.process_file(file, updating = updating)
		else:
			self.process_file(filepath, updating = updating)

		self.write_appinfo(self.appinfo)

		return self.appinfo


	def write_appinfo(self, appinfo):
		with dag.dtprofiler("write_appinfo"):
			with dag.file.open(APPINFO_PATH, "w") as file:
				file.write(json.dumps(appinfo))

		self.appinfo = appinfo


	def unregister_filepath(self, filepath):
		for cmd, values in copy.copy(self.appinfo).items():
			if values[FILEPATH] == str(filepath):
				del self.appinfo[cmd]

		self.write_appinfo(self.appinfo)


	def reregister_updated_pathfiles(self) -> None:
		"""
		Check for files that have been updated since last initialization and re-register them with updated info
		"""

		files = self.get_modified_pathfiles()

		if files:
			for filepath in files:
				self.unregister_filepath(filepath)
				self.register(filepath, updating = True)


	def get_modified_pathfiles(self):
		updated = set()

		for cmd, values in self.appinfo.items():
			filepath = pathlib.Path(values[FILEPATH])

			if filepath in updated:
				continue

			filelastregistered = values[LASTMODIFIED]
			filelastmodifiedtime = os.path.getmtime(filepath)

			if filelastmodifiedtime > filelastregistered:
				updated.add(filepath)

		return list(updated)


	def remove_deleted_pathfiles(self) -> None:
		"""
		Check for registered files that no longer exist and remove from appinfo
		"""

		files = self.get_pathfiles()

		is_deleted_files = False
		for file in files:
			if not file.exists():
				is_deleted_files = True
				self.appinfo = {k: v for k, v in self.appinfo.items() if v[FILEPATH] != str(file)}

		if is_deleted_files:
			self.write_appinfo(self.appinfo)


	def get_pathfiles(self):
		"""
		Get all files that are associated with registered identifiers
		"""

		return list(set([dag.Path(a[FILEPATH]) for a in self.appinfo.values()]))


	def check_pathinfo_for_new_files(self):
		"""
		Check the dag path for new files and register any new ones
		"""

		def maybe_register_file(file: pathlib.Path) -> None:
			"""
			Register the file if it isn't already registered
			:param file: The file to possibly register
			"""
			nonlocal files

			if file not in files:
				self.register(file)

		files = self.get_pathfiles()

		# IF Pathinfo exists: Read the pathinfo and process the files/directories
		if dag.file.exists(dag.PATHINFO_PATH):
			# FOR each entry in pathinfo: Process the item
			for line in dag.file.readlines.RAW(dag.PATHINFO_PATH):
				path = dag.Path(line)
				# IF the path is a directory: Process all files with in the directory
				if path.is_dir():
					for file in path.iterdir():
						if not file.suffix == ".py" or file.stem == "__init__":
							continue

						maybe_register_file(file)
				# ELSE, path is not a directory: Process the individual file
				elif path.exists():
					maybe_register_file(path)