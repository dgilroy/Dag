import dag

from dag.util import mixins, persistencefile


ext = dag.config.CACHEFILE_EXT + ".gz"

class DagCmdExCtxPersistenceFile(persistencefile.PersistenceFile):
	def __init__(self, file_root_dir):
		super().__init__(file_root_dir)


	def generate_filename_from_dagcmd_exctx(self, exctx):
		filename = ""

		if exctx.parsed:
			argnames = sorted(exctx.parsed.keys())

			for argname in argnames:
				if not (dagarg := exctx.dagcmd.dagargs.get(argname)) or dagarg.settings and not dagarg.settings.cacheable:
					continue

				parsedvalue = exctx.parsed[argname]

				if not parsedvalue:
					continue 

				if isinstance(parsedvalue, mixins.CacheFileNamer):
					parsedvalue = parsedvalue._dag_cachefile_name()

				filename += f"--{argname}-{parsedvalue}"

		return self.format_filename_chars(f"{filename}.{ext}")


	def get_folder_filename_from_dagcmd_exctx(self, exctx):
		folder = exctx.dagcmd.cmdpath().lower()
		filename = self.generate_filename_from_dagcmd_exctx(exctx).strip("/")

		return folder, filename


	def exists_from_dagcmd_exctx(self, exctx):
		folder, filename = self.get_folder_filename_from_dagcmd_exctx(exctx)
		return super().exists(folder, filename)


	def read_from_dagcmd_exctx(self, exctx):
		folder, filename = self.get_folder_filename_from_dagcmd_exctx(exctx)
		return super().read(folder, filename)


	def write_from_dagcmd_exctx(self, text, exctx):
		folder, filename = self.get_folder_filename_from_dagcmd_exctx(exctx)
		return super().write(text, folder, filename)


	def write_from_ic_response(self, ic_response):
		return self.write_from_dagcmd_exctx(ic_response.raw_response, ic_response.incmd)



CacheFile = DagCmdExCtxPersistenceFile(dag.config.CACHEFILE_DIR)
#TempCacheFile = DagCmdExCtxPersistenceFile(dag.config.TEMPCACHE_DIR)