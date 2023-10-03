import traceback, json

import dag
from dag.lib import concurrency
from dag.util.mixins import Alistable

from dag import tempcache
from dag.dagcli import outputprocessors
from dag.exceptions import DagError, DagFalseException, DagExitDagCmd

from dag.parser.inputscripts import InputScript
from dag.parser.icresponses import InputCommandResponse
from dag.parser.incmdlists import InputCommandList
from dag.parser.incmds import InputCommand
from dag.parser import dagargparser


class InputScriptExecutor:
	def __init__(self, inscript: InputScript):
		self.inscript = inscript
		self.last_incmd = None
		self.last_ic_response = None
		self.last_exception = None

		self.last_response = None
		self.last_response_no_multicol = None


	def execute(self) -> InputCommandResponse | None:
		for incmdlist in self.inscript.yield_incmdlists():
			iclistexecutor = InputCommandListExecutor(self, incmdlist)
			last_ic_response = iclistexecutor.execute()

			self.last_icresponse = last_ic_response or None
			self.last_incmd = iclistexecutor.last_incmd
			self.last_response = last_ic_response.response if last_ic_response else  ""
			self.last_response_no_multicol = last_ic_response.response_no_multicol if last_ic_response else ""

		return self.last_icresponse


#>>>> InputCommandListExecutor
class InputCommandListExecutor:
	def __init__(self, inscriptexecutor: InputScriptExecutor, iclist: InputCommandList):
		self.inscriptexecutor = inscriptexecutor
		self.iclist = iclist

		self.last_incmd = None
		self.last_icresponse = None
		self.last_response = None
		self.last_response_no_multicol = None

		self.active_exception = None
		self.last_exception = None

		self.piped_responses = []


	def execute(self) -> InputCommandResponse | None:
		ic_response = None

		with dag.ctx(piped_responses = self.piped_responses):
			for incmd in self.iclist.yield_incmds():
				try:
					try:
						if self.last_exception and self.last_incmd.terminus is dag.parser.Token.AND_IF:
							continue
						elif self.last_incmd and not self.last_exception and self.last_incmd.terminus is dag.parser.Token.OR_IF:
							self.last_exception = None
							continue
						icexecutor = InputCommandExecutor(self, incmd)
						ic_response = icexecutor.execute()
						dag.instance.controller.last_incmd = incmd
						dag.instance.controller.last_ic_response = ic_response # Set here so that commands with semicolons  (e.g. "password-genrate ; >") work
						self.last_icresponse = ic_response or self.last_icresponse
						self.last_response = dag.get_terminal().strip_escape_codes(str(self.last_icresponse.response or "")) or ""
						self.last_response_no_multicol = self.last_icresponse.response_no_multicol or ""

						if incmd.is_piped:
							self.piped_responses.append(ic_response.raw_response)

						# If we made it this far, then there were no exceptions. Indicate that here
						self.last_exception = None
					except (Exception, BaseException) as e:
						self.active_exception = e
						self.last_exception = e
						self.inscriptexecutor.last_exception = e
						raise e

				except OSError as e:
					dag.instance.view.echo(e)
					continue
				except DagError as e:
					dag.instance.view.echo(f"<c bold>DagError: execution halted:</c>\n\n")
					#dag.print_traceback()
					#breakpoint()

					dag.instance.view.echo(f"\n<c red>{e}</c>")
					continue
				except DagFalseException as e:
					response = False
					ic_response = incmd.generate_response(response, {})
					dag.instance.view.echo(response)
					continue
				except DagExitDagCmd:
					print("exiting cmd")
					continue
				finally:
					if incmd.is_should_store_input_info:
						self.last_icrsponse = ic_response
						self.last_incmd = incmd

			return self.last_icresponse
#<<<< InputCommandListExecutor


class InputCommandExecutor:
	def __init__(self, iclistexecutor: InputCommandListExecutor, incmd: InputCommand) -> None:
		self.iclistexecutor = iclistexecutor
		self.incmd = incmd


	def execute(self) -> InputCommandResponse | None:
		with dag.ctx(self.incmd.dagcmd.cmdpath("_")):
			incmd = self.incmd
			parsed = incmd.raw_parsed

			with dag.ctx(active_dagcmd = incmd.dagcmd, active_incmd = incmd, directives = incmd.directives, pipe_active = incmd.is_piped):
				if not dag.ctx.skip_type_parser:
					typedparser = dagargparser.TypedParser(incmd)
					parsed = typedparser.parse()

				for newparsed in incmd.expand_parsed(parsed):
					response = self.execute_parsed_incmd(incmd, newparsed)

				return response
				#return self.execute_parsed_incmd(incmd, parsed)


	def execute_parsed_incmd(self, incmd, parsed) -> InputCommandResponse | None:
		response = None
		ic_response = None

		with dag.ctx(parsed = parsed):
			# Search for metadirectives
			response = incmd.inputargs.execute("process_incmd_meta", incmd, parsed,  _inputobj_execution_breaker = lambda x: x is not None,)

			# If response is none: No meta data was present. Execute the dagcmd
			if response is None:
				#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
				# Before Running Command
				#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
				# if tempcache requested and not to be updated and tempcache data already exists: get tempcached response if it exists and requested
				if incmd.do_read_from_tempcache:
					response = tempcache.tempcachefiles.read_from_dagcmd_exctx(incmd)

				#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
				# Run dagcmd
				#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
				dag.instance.view.pre_incmd_execute(incmd, parsed)
				ic_response = incmd.generate_response(response, parsed)

				#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
				# After running dagcmd
				#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
				# If response is dag.Error: Print error and return
				if isinstance(ic_response.raw_response, dag.Error):
					dag.instance.view.echo(f"DagError: <c red / {ic_response.raw_response.message}>")
					return ic_response
				# If display styling hasn't been disabled: Style the response for CLI display
				if not dag.settings.noformat and not incmd.is_piped and not incmd.terminus is dag.parser.Token.DOUBLE_SEMICOLON:
					ic_response.generate_formatted_response_for_cli(parsed)

				# If tempcache had been requested: Append response saying so
				if incmd.do_read_from_tempcache:
					ic_response.prepend_response("<c red/Reading from tempcache\n----------------------------\n\n>")

				processed_response = incmd.outputprocessor.process_output(ic_response, self)

				# If tempcache is enabled on dagcmd and response wasn't read from tempcache: Write to TempCache, if possible
				if False and incmd.do_write_to_tempcache:
					try:
						tempcache.tempcachefiles.write_from_dagcmd_exctx(ic_response.raw_response, incmd)
						#concurrency.run_multiprocess_task(tempcache.tempcachefiles.write_from_dagcmd_exctx, [ic_response.raw_response, incmd]) -> keeps being buggy
					except Exception as e:
						dag.instance.view.echo(f"\n\n<c red>Could not write to tempcache ({e})</c>")
						pass

				# If processed_response is None: The output is meant for CLI. Process accordingly
				if processed_response is None:
					dag.instance.controller.process_dagcmd_response_for_cli(ic_response, self)
					
			# Else, meta data was present: Style and output the data
			else:
				ic_response = incmd.generate_response(response, parsed)
				incmd.outputprocessor.process_output(ic_response, self)

			return ic_response