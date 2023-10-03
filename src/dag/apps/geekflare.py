import dag
from dag import r_



geekflare = dag.app.JSON("dns", baseurl = "https://api.geekflare.com/", auth = dag.auth.HEADER("x-api-key", dag.nab.env.GEEKF_TOK))

#dnscheck = geekflare.cmd("dnscheck").DEFAULT.POST("dnsrecord", r_.data, json = {"url": dag.args.domain}) -> For some reason this returns a 400 error

@geekflare.DEFAULT.cmd.POST("dnsrecord", r_.data, json = {"url": dag.args.domain})
def dnscheck(domain):
	return


@dnscheck.display
def display_dnscheck(response, formatter, parsed):
	formatter.col(0, padding_left = 4, id = "dnsrecord")
	formatter.add_message(f"\n\n<c u #F00>DOMAIN: {parsed.domain}</c u #F00>")

	for recordtype, records in response.items():
		if not records:
			continue

		formatter.add_row(recordtype, style = "b")

		with dag.catch():
			for record in records:
				if isinstance(record, str):
					formatter.add_row(" "*4 + record, id = "dnsrecordtext")
				elif dag.is_mapping(record):
					formatter.add_row(*[k.upper() for k in record.keys()], style="b magenta1", id = f"dnsrecord-{recordtype}", padding_left = 4)
					formatter.add_row(*[str(v) for v in record.values()], style="b #FDD", id = f"dnsrecord-{recordtype}", margin_bottom = 2, padding_left = 4)
					#formatter.add_row(" "*4 + name.upper() + ":", str(value), style="b #FDD", id = "dnsrecord")
					#formatter.add_row(" "*4 + str(value), id = "dnsrecord", margin_bottom = 2)

	formatter.add_message(f"\n\n<c u #F00>/DOMAIN: {parsed.domain}</c u #F00>")