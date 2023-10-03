import dag
from dag import r_


nps = dag.app("nps", baseurl = "https://developer.nps.gov/api/v1/", auth = dag.auth.HEADER("X-Api-Key", dag.nab.env.NPS_TOK))

parks = nps.collection.GET("parks", r_.data)