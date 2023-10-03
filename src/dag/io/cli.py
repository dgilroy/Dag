import subprocess, getpass, shlex, re
from contextlib import contextmanager

import dag
from dag.lib import concurrency
from dag.util import prompter

from dag.exceptions import DagSubprocessRunError
from dag.responses import parse_response_item


def raise_subproc_error(response):
	raise DagSubprocessRunError(f"<c u>Dag Cli Return Code: {response.returncode}</c u>\n  "+ str(response.stderr)[2:-3])


def subproc(action, commands):
	def _do_subprocess(args):
		#action = args.pop(0)
		dag.echo(f"RUNNING {args}\n")
		try:
			response = action(shlex.split(args + " ")) # Space added so that files ending with '\' don't complain about no escaped character
			if response.returncode:
				raise_subproc_error(response)
		except OSError as e:
			dag.echo('cmd exception: ', e)

	is_str = isinstance(commands, str)
	commands = [commands] if is_str else commands 
	
	dag.hooks.do("pre_run", commands)
	response = concurrency.multithread_map(_do_subprocess, commands)
	dag.hooks.do("post_run", response)
	
	return response[0] if is_str else response




def popen(commands, threaded = False, stdout = subprocess.PIPE, stderr = subprocess.PIPE, debug = False, wait = True, silent = False, background = False):
	if background:
		wait = False
		silent = True

	is_str = isinstance(commands, str)

	if not threaded:
		return subproc(subprocess.Popen, commands)

	if silent:
		stdout = subprocess.DEVNULL
		stderr = subprocess.DEVNULL

	process = [subprocess.Popen(command, shell = True, stdout= None if debug else stdout, stderr = None if debug else stderr) for command in commands]

	[dag.echo(f"running command: <c b u>{command}</c>") for command in commands]

	if wait:
		for p in process:
			p.wait()

		response = []

		for p in process:
			try:
				response.append(parse_response_item(p.communicate()[0].decode("utf-8")))
			except Exception as e:
				#breakpoint()
				pass

		#response = [parse_response_item(p.communicate()[0].decode("utf-8")) for p in process]

		return response[0] if is_str else response


def do_subprocess_call(args: list[str], pipe: bool = False, **kwargs) -> str:
	response = "Dag Pipe: No Response" if pipe else ""
	stdout = subprocess.PIPE if pipe else None
	stderr = subprocess.PIPE if pipe else None

	args = dag.parser.lexer.token_split(args.strip(), ";")

	for arg in args:
		try:
			if not arg:
				continue

			output = subprocess.run(shlex.split(arg), stdout=stdout, stderr=stderr)
			#if output.returncode:
			#	raise_subproc_error(output)

			if output.stdout:
				response = output.stdout.decode("utf-8").strip() # ONLY LAST RESPONSE WILL BE SENT
			elif output.stderr:
				response = "\n\n<c red underline>DAG CMD ERROR:		</c underline>\n" + output.stderr.decode("utf-8").strip() + "</c>" # ONLY LAST RESPONSE WILL BE SENT	

		except OSError as e:
			dag.echo('cmd exception: ', e)

	return response



@dag.iomethod(name = "run", group = "cli")
def run(args: list[str], **kwargs) -> None:
	do_subprocess_call(args, pipe = False, **kwargs) # Run doesn't return anything


@dag.iomethod(name = "pipe", group = "cli")
def pipe(args: list[str], **kwargs) -> str:
	return do_subprocess_call(args, pipe = True, **kwargs)



def bell():
	dag.echo('\a')



### PROMPTING ###		
def prompt(message = "", **kwargs):
	return dag.instance.view.promptclass(message + (kwargs.get("suffix", "")), **kwargs).prompt()


def prompt2(message = "", suffix = "", **kwargs):
	return prompter.prompt(message + suffix, **kwargs)



def confirm(message, *args, confirmer = None, force = False, suffix = "", use_getch = True, confirmval = None, **kwargs):
	if force or dag.settings.force:
		return True

	if confirmval:
		confirmer = lambda x: x == confirmval
		suffix = suffix or f" (type <c green1 i b>{confirmval}</c green1 i b> to proceed)"
		use_getch = False
	elif confirmer is None:
		confirmer = lambda x: x.lower().startswith("y")
		suffix = suffix or " (Press <c green1 i b>\"y\"</c green1 i b> for yes)"

	try:
		while True:
			if use_getch:
				val = getch(message + suffix)
			else:
				val = prompt(message + suffix)
			#val = prompt(*args, suffix = suffix, **kwargs)
			if val:
				break
	except (Exception, BaseException):
		return False

	return confirmer(val)


def confirmprompt(*args, **kwargs):
	return confirm(*args, use_getch = False, **kwargs)


def password(message):
	return getpass.getpass(f"{message} (hidden): ") 


def passwordverify(message, message2 = ""):
	if not message2:
		message2 = re.sub(r"[eE]nter", "Re-enter", message) if "nter" in message else f"Re-enter {message}"

	while True:
		val1 = getpass.getpass(f"{message} (hidden): ") 	
		val2 = getpass.getpass(f"{message2} (hidden): ") 	
		if val1 == val2:
			break

		dag.echo("\n<c bu>The two entries didn't match. Please try again</c bu>\n")


@contextmanager
def confirmer(*args, force = False, **kwargs):
	val = False
	if force:
		val = True
	else:
		val = confirm(*args, **kwargs)

	yield val

	if not val:
		dag.echo("No action taken")



def getch(message = "CHAR"):
	import tty, termios, sys
	fd = sys.stdin.fileno()
	old_settings = termios.tcgetattr(fd)
	try:
		dag.echo(message)	
		tty.setraw(sys.stdin.fileno())
		ch = sys.stdin.read(1)
	finally:
		termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
	return ch