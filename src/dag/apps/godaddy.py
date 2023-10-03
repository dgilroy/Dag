import dag



godaddy = dag.app.JSON("godaddy", baseurl = "https://api.godaddy.com/v1/", doc = "https://developer.godaddy.com/doc",
			auth = dag.auth.HEADER(prefix = "sso-key ", token = dag.nab.env.GD_KEY + ":" + dag.nab.env.GD_SEC))

domains = godaddy.DEFAULT.collection("domains", launch = "https://dcc.godaddy.com/domains").GET("domains?limit=1000")
domains.resources.label("domain").id("domainId").launch("https://dcc.godaddy.com/control/{domain}/settings")