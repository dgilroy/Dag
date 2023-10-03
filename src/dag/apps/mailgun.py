import dag
from dag import r_



mailgun = dag.app.JSON("mailgun", baseurl = "https://api.mailgun.net/", doc = "https://documentation.mailgun.com/en/latest/index.html",
			auth = dag.auth.BASIC("api", dag.nab.env.MG))


domains = mailgun.DEFAULT.collection("domains").GET("v4/domains", r_.items)
domains.resources("domain").launch("https://app.mailgun.com/app/sending/domains/{name}/logs").id("id").label(r_.name.split(".")[1])


dns = domains.op("dns").GET("v4/domains/{domain.name}")
verify = domains.op("verify", callback = mailgun.dns.partial(dag.args.domain)).PUT("v4/domains/{domain.name}/verify")
logs = domains.op("logs").LAUNCH("https://app.mailgun.com/app/sending/domains/{domain.name}/logs")


@dns.display
def display_dns(response, formatter):
	formatter.add_message("Sending domains")

	for domain in response.sending_dns_records:
		is_valid = domain.valid == "valid"
		rowstyle = "#DFD" if is_valid else "#FDD"
		prefix = "<c green>✓</c>" if is_valid else "<c #F00>X</c>"
		formatter.add_row(prefix + " " + domain.record_type, style = rowstyle)
		formatter.add_row(domain.name, style = rowstyle)
		formatter.add_row(domain.value, style = rowstyle, margin_bottom = 2)