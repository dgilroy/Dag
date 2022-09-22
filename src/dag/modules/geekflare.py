import dag
from dag import this



@dag.mod("dns", baseurl = "https://api.geekflare.com/", default_cmd = this.dnscheck, auth = dag.auth.OTHER("x-api-key", dag.nab.env.GEEKF_TOK), response_parser = dag.JSON)
class GeekFlare(dag.DagMod):
	
	@dag.arg("domain")
	@dag.cmd(value = dag.nab.post("dnsrecord", json = {"url": dag.arg("domain")}).data, display = this._display_dnscheck)
	def dnscheck(self, domain):
		return


	def _display_dnscheck(self, response, formatter, parsed):
		formatter.col(0, padding_left = 4, id = "dnsrecord")
		formatter.add_message(f"\n\n<c u #F00>DOMAIN: {parsed.domain}</c u #F00>")

		for recordtype, records in response.items():
			if not records:
				continue

			formatter.add_row(recordtype, style = "b")

			with dag.catch():
				for record in records:
					if isinstance(record, str):
						formatter.add_row(" "*4 + record, id = "dnsrecord")
					elif record.is_dict():
						for name, value in record.items():
							formatter.add_row(" "*4 + name.upper(), style="b #FDD", id = "dnsrecord")
							formatter.add_row(" "*4 + str(value), id = "dnsrecord", margin_bottom = 2)
						formatter.add_row("    --\n")

		formatter.add_message(f"\n\n<c u #F00>/DOMAIN: {parsed.domain}</c u #F00>")