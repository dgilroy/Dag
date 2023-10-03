import dag



envato = dag.app.JSON("envato", baseurl = "https://api.envato.com/v3/", doc = "https://build.envato.com/api",
			auth = dag.auth.HEADER(prefix = "Bearer ", token = dag.nab.env.ENVAT_TOK))


purchases = envato.DEFAULT.collection("purchases", launch = "https://themeforest.net/downloads").GET("market/buyer/list-purchases", "results")
purchases.resources('purchase').launch("{item.url}").id("code").label("item.name")


@purchases.display
def display_purchases(response, formatter):
	for purchase in formatter.idxitems(response):
		formatter.add_row(purchase.item.name)


@purchases.op
def download(purchase):
	return dag.get(f"market/buyer/download?item_id={purchase.item.id}")