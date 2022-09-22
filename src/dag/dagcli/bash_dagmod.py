import re, os, pathlib
from subprocess import run

import dag
from dag import this



@dag.mod("bash", base = True, raw = True, enable_tempcache = False, complete = this._complete())
class Bash(dag.DagMod):

	@dag.arg.Directory('dir', use_str = True)
	@dag.cmd(catch = (FileNotFoundError))
	def cd(self, dir, *args):
		# If input is something like "C:", make it "C:/" to properly change drives
		if re.match("[a-zA-Z]:$", dir):
			dir = dir + "/"
			
		os.chdir(dir)


	def _complete(self):
		path = None

		if dag.ctx.parsed:
			argname, argval = list(dag.ctx.parsed.items())[-1]
			path = pathlib.Path(argval)
			path = str(path.parent if not argval.endswith("/") else path)

		return os.listdir(path)


	@dag.arg.Directory('dir')
	@dag.cmd()
	def take(self, dir):
		"""
		Based on zsh: go to directory, making it if necessary

		:param dir: The directory to create and/or change into
		"""

		# If dirpath has a suffix, then the final part is a file. So take the file's parent directory
		dir = dir if not dir.suffix else Path(dir).parents[0]

		dir.mkdir(parents=True, exist_ok=True) 

		os.chdir(dir)


	@dag.arg.File('path')	
	@dag.cmd()	
	def npp(self, path, *args):
		self._run_cmd("notepad++.exe", path, *args)


	@dag.arg.Path('path', native_path = True)
	@dag.cmd()
	def photoshop(self, path = "", *args):
		self._run_cmd("Photoshop.exe", path, *args)


	@dag.arg.Directory('path')
	@dag.cmd()
	def explorer(self, path = ".", *args):
		self._run_cmd("explorer", path, *args)


	@dag.arg.File('path')	
	@dag.cmd()
	def irfanview(self, path = "", *args):
		dag.cli.popen(f"i_view32.exe {path}", *args)


	@dag.cmd()
	def ftp(self):
		dag.cli.popen(f"{dag.config.FTP_PROGRAM}")


	@dag.arg.Path('path')
	@dag.cmd('which', 'rm', "vim", "cat", "ls")
	def _run_cmd_with_path(self, path = "", *args):
		self._run_cmd(dag.ctx.active_dagcmd.name, path, *args)


	@dag.arg("command", complete = ["status", "diff"])
	def git(self, command = "", *args):
		self._run_cmd("git", command, *args)


	@dag.cmd('python', 'touch', 'mkdir', 'pwd', 'grep', "cal", "find", "echo", "lynx", "ps", "xargs", "pytest", "pip")
	def _run_cmd_nopath(self, *args):
		self._run_cmd(dag.ctx.active_dagcmd.name, *args)

	@dag.cmd()
	def dagtest(self, *args):
		self._run_cmd("pytest /dag/tests", *args)


	@dag.cmd()
	def sourcebash(self):
		dag.cli.run("source ~/.bashrc")


	def _run_cmd(self, cmd, *args):
		try:
			return self.run_line_in_bash(f"{cmd} {' '.join([str(a) for a in args])}")
			#dag.cli.run(f"{cmd} {' '.join(args)}")
		except OSError as e:
			breakpoint()
			return print('DAG command exception: ', e)

	#@dag.arg("line", nargs = -1, nargs_join = " ")
	#@dag.cmd("!")
	def run_line_in_bash(self, line):
		try:
			dag.cli.run(line)
		except OSError as e:
			breakpoint()
			return print('Bash dagmod exception: ', e)