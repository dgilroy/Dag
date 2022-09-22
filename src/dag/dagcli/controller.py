import sys, traceback, subprocess

import dag
from dag.lib import concurrency
from dag.util import dagdebug
from dag.util.historyfile import dag_historyfile
from dag.util.mixins import DagFiltable, DagDrillable, Alistable
from dag.util.drill import DagDrillError

from dag.dagcli import filts, helpformatter
from dag.dagcli.alist import Alist

from dag import tempcache
from dag.parser import DagArgParser, InputScript, lexer, InputCommand

from dag.dag_controller import DagController
from dag.exceptions import DagError, DagInvalidCommandException, DagFalseException, DagReloadException, DagMultipleCommaListException

from dag.dagcmds import DagCmd

from dag.modules import *

 # Currently handles: (1) Executing the line (2) providing services to handle output in the console (eg: Copying, opening in browser, open documentation) (3) Registers Commands (4) Holds History
class DagCLIController(DagController):

	def __init__(self, view):
		with dag.ctx(controller = self):
			self.view = view

			self.register_commands()

			self.last_line = None
			self.last_incmd = None
			self.last_ic_response = None

			dag_historyfile.load_into_readline()



	# Adds proper commands to command_table
	def register_commands(self):
		# Importing internally-important DagMods
		from dag import pathmanager_dagmod
		from dag.dagcli import bash_dagmod, base_cli_dagmod

		# Register Dagmods as commands, linking the name to their own module name (compare with __alist cmds) #
		for dagmod_name, dagmodcls in dag.default_dagcmd.imported_cmds.items():
			dag.get_dagcmd(dagmod_name) # get_dagcmd initializes the dagmods


		# Register base dagmod commands #
		for dagmod_name, dagmodcls in dag.default_dagcmd.subcmdtable.children.dagmods.items():
			if dagmodcls.settings.get("base"):
				dagmod = dag.get_dagcmd(dagmod_name)

				for dagcmd in dagmod.subcmdtable.values():
					# Skip parent dagcmds
					try:
						if dagcmd.settings.parentcmd:
							continue
					except Exception as e:
						breakpoint()
						pass
					
					if dagcmd.name in dag.default_dagcmd.subcmdtable.names():
						breakpoint()
						raise DagError(f"Command \"{dagcmd.name}\" already registered in Dag")
						
					dag.default_dagcmd.subcmdtable.children.base_dagcmds.add(dagcmd)


	# Complete #
	def complete_line(self, line, debugmode = False):
		from dag.dagcli import completer # speed up dag load
		# *_ is from PEP448 (see https://stackoverflow.com/questions/2138873/cleanest-way-to-get-last-item-from-python-iterator)
		incmd = InputScript.generate_from_text(line).get_last_incmd()

		if not incmd.init_attempts:
			incmd.initialize()

		with dag.ctx(active_dagcmd = incmd.dagcmd):
			#incmd.run_parser(parse_while_valid = True) #-> Removed for now since it's interfering with "M new" completion (it thinks new is a Resource for the Collection)
					
			return completer.dag_complete(incmd, debugmode)


	# UTILITIES #			
	def run_incmd(self, incmd):
		# Populate incmd info (This needs to be done one-at-a-time so that ALIST commands work right) 
		if incmd.init_attempts == 0:
			incmd.initialize()

		# Checks is_empty and dagmod, bc sometimes I want to insert dagmod after initialization, like in after/callbacks
		if incmd.is_empty() and not incmd.dagcmd:
			return

		directives = incmd.directives

		response = None
		ic_response = None


		with dag.ctx(active_dagcmd = incmd.dagcmd):
			try:
				if incmd.directives.executor:
					ic_response = incmd.execute()
					return self.process_ic_response(ic_response)

				# Else, parse input and so run the command
				else:
					try:
						if not incmd.parsed: # parsed can come from callback for things like ticket replies
							incmd.validate_args_input_formatting()
							incmd.run_parser()
					except Exception as e:
						raise e
						return incmd.generate_response(f"{type(e)}: {e}")

				dagcmd = incmd.dagcmd

				if incmd.dagcmd.settings.get("confirm"):
					if dag.cli.confirm(message = incmd.dagcmd.settings.confirm.format(**incmd.parsed) + " <c white>(y/n)</c white>"):
						pass
					else:
						print("NO ACTION TAKEN")
						return


				with dag.ctx(parsed = incmd.parsed):

					##################################################
					# Before Running Command
					##################################################
					if not response:
						# else, if tempcache requested, get tempcached response if exists and requested
						if incmd.directives.tempcache and not incmd.directives.update_dagcmd_cache and tempcache.TempCacheFile.exists_from_dagcmd_exctx(incmd):
							response = tempcache.TempCacheFile.read_from_dagcmd_exctx(incmd)

						# else, get help text if requested
						elif incmd.directives.help_active:
							response = self.man(incmd.dagcmd.name)

						# else, launch API documentation if requested
						elif directives.api_documentation_active:
							response = self.launch_apidoc(incmd)

						# Run Before Command
						if dagcmd.settings.get("before") is not None:
							self.view.echo((dagcmd.settings.before))

						incmd.directiveexecutor.preprocess_incmd_directives()

					########################################
					# Run dagcmd
					########################################
					with dag.ctx(directives = directives, active_incmd = incmd):
						ic_response = incmd.generate_response(response)

					##################################################
					# After running dagcmd
					##################################################
					if not incmd.do_copy and not incmd.dagcmd.name == "last":
						self.last_incmd = incmd or self.last_incmd

					return self.process_ic_response(ic_response)

			finally:				
				if ic_response:
					self.last_ic_response = ic_response or self.last_ic_response
					self.last_response = dag.get_terminal().strip_escape_codes(str(self.last_ic_response.response or "")) or ""
					self.last_response_no_multicol = self.last_ic_response.response_no_multicol or ""




	def process_ic_response(self, ic_response):
		incmd = ic_response.incmd
		dagcmd = incmd.dagcmd
		directives = incmd.directives

		incmd.directiveexecutor.process_ic_response_directives(ic_response)

		r = ic_response.raw_response

		# If @dag.collection has launch, launch before running dagcmd
		if (directives.do_launch or directives.portalurl): 
			if isinstance(r, dag.Resource) and r._dag.settings.launch:
				# Ugly fix because currently Resource DagArg is calling incmd.dagcmd(*args) and this is messing up parsed args
				#incmd.run_parser()

				# This monstrosity allows for parsed args and resource arg info to be considered together
				url = r._dag.settings.launch.format(**{**incmd.parsed, **incmd.parsed[dagcmd.resource_name]})
				ic_response.response = url
				#return r._dag.settings.launch.format(**incmd.parsed[dagcmd.resource_name])

			if dagcmd.settings.get("launch") is not None:
				ic_response.response = dagcmd.settings.launch.format(**incmd.parsed)


		response = ic_response.raw_response

		if isinstance(response, DagFiltable):
			if incmd.filts_list:
				ic_response = incmd.generate_response(filts.filter(response, incmd))


		if response or isinstance(response, DagDrillable):
			# Drill deeper into response if requested
			if incmd.drillbit:
				try:
					ic_response = incmd.generate_response(dag.drill(response, incmd.drillbit))
				except DagDrillError:
					self.view.echo(f"Invalid drillbit: {incmd.drillbit}")

		# Print URL if requested
		if directives.portalurl:
			ic_response = incmd.generate_response(dag.launcher.get_item_url(response))


		# Write message and format response
		if not directives.noformat and not incmd.drillbit and not directives.launch and not directives.portalurl and not directives.tempcache and not directives.baseurl:
			# Prints a message and formats it with any variables
			self.view.print_incmd_message_if_valid(incmd)

			ic_response.generate_formatted_response_for_cli()


		response_prepend = ""
		response_addon = ""

		# Print keys in response if requested
		if directives.tempcache:
			response_prepend += "Reading from tempcache\n----------------------------\n\n"

		ic_response.response = response_prepend + ic_response.response + response_addon

		# Copy, if requested
		if incmd.do_copy:
			return dag.copy_text(str(ic_response.response_no_multicol or ic_response.response), echo = True)


		# Write response to outfile if requested
		if incmd.outfile_name:
			return self.write_outfile(ic_response)


		# If browser launch requested: Launch response in browser
		if incmd.directives.do_launch:
			self.launch_ic_response(ic_response)


		# Pipe shouldn't print output to terminal: Its response will be fed into something else;
		if incmd.op == lexer.Tokens.PIPE:
			return

		if isinstance(ic_response.raw_response, Alistable) and ic_response.raw_response.settings.idx:
			if not ic_response.formatted_response and not directives.noformat:
				ic_response.generate_formatted_response_for_cli()

			Alist.set(ic_response)



		self.view.print_incmd_response(ic_response)

		# Write to TempCache, if possible
		if incmd.dagcmd.dagmod and incmd.dagcmd:
			if incmd.dagcmd.settings.enable_tempcache and not (incmd.directives.tempcache and not incmd.directives.update_dagcmd_cache and tempcache.TempCacheFile.exists_from_dagcmd_exctx(incmd)):
				try:
					tempcache.TempCacheFile.write_from_ic_response(ic_response)
					#concurrency.run_multiprocess_task(tempcache.TempCacheFile.write_from_ic_response, [ic_response]) -> keeps being buggy
				except Exception as e:
					breakpoint()
					self.view.echo(f"{e}\n\n<c red>Could not write to tempcache</c>")

		# Handle callback
		if incmd.dagcmd.settings.get("callback") is not None:
			callback_incmd = self.run_dagcmd_callback(incmd)
			self.run_incmd(callback_incmd)

		return ic_response


	## Launcher
	def launch_ic_response(self, ic_response):
		incmd = ic_response.incmd
		item = ic_response.raw_response


		url = dag.launch(item, incmd.directives.browser, incmd.directives.portalurl)
		ic_response.response = url



	# Execute command callback	
	def run_dagcmd_callback(self, incmd):
		dagcmd = incmd.dagcmd

		callback = dagcmd.settings.callback

		if not isinstance(callback, DagCmd):
			return callback()

		ic = InputCommand.InputCommand()
		ic.set_dagcmd(callback)

		if callback.locals:
			ic.parsed = callback.locals

		return ic



	# Write text to file
	def write_outfile(self, ic_response):
		with open(ic_response.incmd.outfile_name, "w") as file:
			file.write(dag.get_terminal().strip_escape_codes(str(self.last_ic_response.response or "")) or "")


	def parser(self, line):
		return InputScript.test_line(line)


	def argparser(self, line):
		return InputScript.test_argument_parser(line)
		

	def launch_apidoc(self, incmd):
		if "doc" in incmd.dagcmd.settings:
			return dag.launch(incmd.dagcmd.settings.doc, incmd.directives.browser)
		else:
			return f"No documentation for <c bold>{incmd.dagcmd.cmdpath()}</c>"



	def do_breakpoint(self):
		breakpoint()


	# EXIT
	def exit(self, code = 0):
		return sys.exit(code)
		
	# EOF
	def eof(self):
		self.view.echo("Ctrl + D exit")
		return self.exit()
		

	# MAN #
	def man(self, command):
		if command in dag.get_dagcmd("bash").subcmdtable:
			return subprocess.run(['man', command], capture_output = True).stdout.decode("utf-8")
		else:
			try:
				dagmod = dag.get_dagcmd(command)
			except DagError as e:
				return self.view.echo(f"{e}")

		return helpformatter.generate_help_text(dagmod)
					
								
	def run_incmd_list(self, incmd_list):
		for incmd in incmd_list.yield_incmds():
			try:
				try:
					self.run_incmd(incmd)
				except (Exception, BaseException) as e:
					incmd_list.active_exception = e
					self.last_exception = e
					#self.view.echo(e)
					raise e
			except OSError as e:
				self.view.echo(e)
				continue
			except (EOFError) as e:
				self.view.echo(f"EOF Error: {e}")
				self.exit()
			except RuntimeError as e:
				self.view.echo(f"<c bold>RuntimeError: execution halted:</c>\n\n")
				traceback.print_exc()
				self.view.echo(f"\n<c red>{e}</c>")
			except DagError as e:
				#self.view.echo(f"<c bold>DagError: execution halted:</c>\n\n")
				#traceback.print_exc()
				self.view.echo(f"\n<c red>{e}</c>")
				continue
			except DagFalseException:
				self.view.echo("false")
				continue
			except Exception as e:
				traceback.print_exc()
				self.view.echo(f"<c bold>Exception: {e}</c>")


	def reload(self, reloadargs: str = ""):
		"""
		Raises exception to exit Dag instance so that a new one will start

		:param reloadargs: the args to be passed into the new Dag instance
		:raises DagReloadException: Raises exception that triggers reload
		"""

		raise DagReloadException(reloadargs)


	def run_input_line(self, line: str):
		"""
		Runs the line and records the line in history

		:param line: The line to be executed
		"""
		return self.run_line(line, store_history = True)


	def run_line(self, line: str, store_history: bool = False):
		# If no line, reload Dag
		if not line.strip():
			self.view.echo("<c magenta2 u>Blank Line Detected:</c>")
			return self.reload()

		# If EOF, end session
		if line.lower().strip() in ["eof"]:
			return self.eof()

		if store_history:
			# Add input to history file
			dag_historyfile.add_if_valid(line)

		# Parse line into incmds
		try:
			input_script = InputScript.generate_from_text(line, strip_trailing_spaces = True)

			for incmd_list in input_script.yield_incmd_lists():
				self.run_incmd_list(incmd_list)
		except DagMultipleCommaListException as e:
			return self.view.echo(f"<c b>Error: </c> {e}")


@dag.cmd()
def testmsg(message):
	return(message)