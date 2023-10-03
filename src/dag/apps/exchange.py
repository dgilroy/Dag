import dag
from dag import r_


exchange = dag.app.XML("exchange", baseurl="https://www.ecb.europa.eu/stats/eurofxref/")

rates = exchange.collection(help = "The available exchange rates").GET("eurofxref-daily.xml?" + dag.nab.now().format("%Y-%m-%d"), r_.css("[currency]"))
rates.resources.label("currency")

	
@exchange.DEFAULT.cmd
def curexchange(old: dag.Resource[rates] = rates.nab.find("gbp"), new: dag.Resource[rates] = rates.nab.find("usd")):
#def curexchange(old: dag.Resource[rates] = rates.nab["gbp"], new: dag.Resource[rates] = rates.nab["usd"]):
	"""View scores of this week's games"""

	#Date is added for caching purposes
	#exch = dag.get.CACHE(f"eurofxref-daily.xml", expires = dag.DTime().midnight.tomorrow)
	exch = dag.get.CACHE(f"eurofxref-daily.xml?day={dag.DTime() :%Y%m%d}")

	intorate = float(exch.css(f"[currency={new.currency}]")[0].rate)
	oldrate = float(exch.css(f"[currency={old.currency}]")[0].rate)
	
	return intorate/oldrate
	
	
@curexchange.display.MESSAGE(dag.nab.DTime().format("%m-%d-%Y"))
def display_exchange(response, formatter, parsed, *, amount: float = 1.0):
	return f"{parsed.amount:0.2f} {parsed.old.currency} is {parsed.amount * response:0.2f} {parsed.new.currency}"