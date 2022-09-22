import subprocess, getpass, shlex

import dag
from dag.lib import concurrency
from dag.util import prompter

from dag.exceptions import DagSubprocessRunError
from dag.responses import parse_response_item



def subproc(action, commands):
	def _do_subprocess(args):
		#action = args.pop(0)
		print(f"RUNNING {args}\n")
		try:
			response = action(shlex.split(args + " ")) # Space added so that files ending with '\' don't complain about no escaped character
			if response.returncode:
				raise DagSubprocessRunError(f"DagMod: Process errored with return code: {response.returncode}")
		except OSError as e:
			print('cmd exception: ', e)


	is_str = isinstance(commands, str)
	commands = [commands] if is_str else commands 
	
	dag.hooks.do("pre_run", commands)
	response = concurrency.multithread_map(_do_subprocess, commands)
	dag.hooks.do("post_run", response)
	
	return response[0] if is_str else response




def run(argstr):
	try:
		dag.hooks.do("pre_run", argstr)
		response = subprocess.run(shlex.split(argstr + " ")) # Space added so that files ending with '\' don't complain about no escaped character
		dag.hooks.do("post_run", response)
		if response.returncode:
			raise DagSubprocessRunError(f"DagMod: Process errored with return code: {response.returncode}")
	except OSError as e:
		print('cmd exception: ', e)




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


@dag.iomethod(name = "pipe", group = "cli")
def pipe(args):
	response = ""

	args = args.split(";")
	for arg in args:
		try:
			output = subprocess.run(shlex.split(arg), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			response = output.stdout.decode("utf-8").strip() or "\n\n<c red underline>DAG CMD ERROR:		</c underline>\n" + output.stderr.decode("utf-8").strip() + "</c>" # ONLY LAST RESPONSE WILL BE SENT
		except OSError as e:
			print('cmd exception: ', e)

	return response



def bell():
	print('\a')



### PROMPTING ###		
def prompt(message = "", complete_list = None, display_choices = True, prefill = ""):
	return prompter.prompt(message, complete_list, display_choices, prefill)


def confirm(*args, confirmer = None, **kwargs):
	if confirmer is None:
		confirmer = lambda x: x.lower().startswith("y")

	val = prompt(*args, **kwargs)

	return confirmer(val)

def password(message):
	return getpass.getpass(f"{message} (hidden): ") 