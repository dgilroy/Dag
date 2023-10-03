import re, os, pathlib, platform
from subprocess import run

import dag

 

def dircomplete():
	pathstr = dag.ctx.active_incmd.tokens[-1]
	path = pathlib.Path(pathstr).resolve()
	dag.bb.completetest()
	path = path.parent if not path.is_dir() else path
	return dag.os.get_files(path)


def dirmodifytext(text):
	return text.split("/")[-1].replace(" ", r"\ ")


bash = dag.cmdtemplate(raw = True, enable_tempcache = False, complete = dircomplete, modify_completion_text = dirmodifytext, no_space = True)


@bash.arg.Directory('dirpath', raw = False)
@bash.cmd(catch = (FileNotFoundError))
def cd(dirpath, *args):
	os.chdir(dirpath)


cd.display(message = "Changing directory to: <c bu>{dirpath}</c bu>")


@bash.arg.Directory('dirpath', raw = False)
@bash.cmd(raw = False)
def take(dirpath):
	"""
	Based on zsh: go to directory, making it if necessary

	:param dirpath: The directory to create and/or change into
	"""

	# If dirpath has a suffix, then the final part is a file. So take the file's parent directory
	dirpath = dirpath if not dirpath.suffix else dirpath.parents[0]

	dirpath.mkdir(parents=True, exist_ok=True) 

	os.chdir(dirpath)


@bash.arg.File('path')	
@bash.cmd	
def npp(path, *args):
	run_cmd("notepad++.exe", path, *args)


@bash.arg.Path('path', native_path = True)
@bash.cmd
def photoshop(path = "", *args):
	run_cmd("Photoshop.exe", path, *args)


@bash.arg.Directory('path', resolve = False)
@bash.cmd()
def explorer(path = ".", *args):
	#path = dag.get_platform().path_to_native(path) # This is here for piped args
	run_cmd("explorer.exe", path, *args)


@bash.arg.File('path')	
@bash.cmd
def irfanview(path = "", *args):
	dag.cli.popen(f"i_view32.exe {path}", *args)


@bash.cmd
def ftp():
	if dag.settings.FTP_CLIENT:
		return dag.cli.popen(f"{dag.settings.FTP_CLIENT}")

	return "No FTP Client found. Set '<c b>FTP_CLIENT</c b>' as a setting"


@bash.arg.Path('path')
@bash.cmd('rm', "vim", "ls", "wc", "tail", "cat", "du", "mv")
def run_cmd_with_path(path = "", *args):
	# If filename starts with a dash: Treat as if it's a flag
	if path.stem.startswith("-"):
		args = (path.stem, *args)
		path = ""

	run_cmd(dag.ctx.active_dagcmd.name, os.path.expanduser(path), *args)


@bash.arg.GreedyWords("command", complete = ["status", "diff"])
@bash.cmd
def git(command = "", *args):
	run_cmd("git", command, *args)


@bash.cmd('touch', 'mkdir', 'pwd', 'grep', "cal", "find", "lynx", "ps", "xargs", "pytest", "ps", "top")
def run_cmd_nopath(*args):
	run_cmd(dag.ctx.active_dagcmd.name, *args)


@dag.cmd
def python(*args):
	pyversion = ".".join(platform.python_version().split(".")[:2])
	run_cmd("python" + pyversion, *args)	


@bash.cmd
def echo(*args):
	from expandvars import expandvars 
	run_cmd(dag.ctx.active_dagcmd.name, *[expandvars(a) for a in args])


@bash.cmd
def dagtest(*args):
	run_cmd("pytest /dag/tests", *args)

@bash.cmd
def branch():
	return dag.cli.pipe("git branch --show-current")


@bash.cmd
def sourcebash():
	dag.cli.run("source ~/.bashrc")


def run_cmd(cmd, *args):
	try:
		return run_line_in_bash(f"{cmd} {' '.join([str(a) for a in args])}")
		#dag.cli.run(f"{cmd} {' '.join(args)}")
	except OSError as e:
		breakpoint()
		return dag.echo('DAG command exception: ', e)


@dag.arg.GreedyWords("line")
@bash.cmd("bash", "r/!.*/")
def run_line_in_bash(line):
	line = line.lstrip("!")

	if dag.strtools.is_valid_quoted_string(line):
		line = dag.strtools.stripquotes(line)

	try:
		dag.cli.run(line)
	except OSError as e:
		breakpoint()
		return dag.echo('Bash dagmod exception: ', e)


@bash.arg.Msg("msg")
@bash.cmd
def gitcommpush(msg):
	run_cmd(f'git commit -am {msg}') # Since bash is raw, the quotes dont get stripped from the msg arg
	run_cmd(f'git push')


@dag.arg.GreedyWords("message", prompt = "Enter commit message")
@bash.cmd("gitcom")
def gitcom(message):
	run_cmd(f"git commit -am '{message}'") # Since bash is raw, the quotes dont get stripped from the msg arg
	run_cmd(f'git push')