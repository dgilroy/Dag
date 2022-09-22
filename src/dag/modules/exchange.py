import dag
from dag import this



@dag.mod("exchange", default_cmd = this.exchange, response_parser = dag.XML, baseurl="https://www.ecb.europa.eu/stats/eurofxref")
class Exchange(dag.DagMod):
	@dag.resources(label = "currency")
	@dag.collection(value = dag.nab.get("eurofxref-daily.xml").css("[currency]"))
	def rates(self):
		"""The available exchange rates"""
		return

		
	@rates("new")
	@rates("old")
	@dag.arg("amount", type = float)
	@dag.cmd(display = this._display_exchange, message = dag.nab.DTime().format("%m-%d-%Y"))
	def exchange(self, amount = 1, old = "gbp", new = "usd"):
		"""View scores of this week's games"""
		exch = dag.get("eurofxref-daily.xml")

		intorate = float(exch.css(f"[currency={new.currency}]")[0].rate)
		oldrate = float(exch.css(f"[currency={old.currency}]")[0].rate)
		
		return oldrate/intorate
		
		
	def _display_exchange(self, response, formatter, parsed):
		breakpoint()
		return f"{parsed['amount']:0.2f} {parsed['old'].currency} is {response:0.2f} {parsed['new'].currency}"