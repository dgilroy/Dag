import dag
from dag import r_



curator = dag.app.JSON("curator", baseurl = "https://api.curator.io/v1/", auth = dag.auth.BASIC(dag.nab.env.CURATORIO_APIKEY), dateformat = "%Y-%m-%d")


feeds = curator.DEFAULT.collection("feeds").GET("feeds")
feeds.resources("feed").label("slug").id("id")


sources = curator.collection("sources").GET("sources")
sources.resources("source").id("id").label("name")
#sources.resources("source", ID = "id", LABEL = "name")


posts = feeds.op("posts").collection.GET("feeds/{feed.id}/posts", r_.posts)
posts.resources.id("id")


"""
curator.add_dagcmds(
	feeds 		= curator | DEFAULT | COLLECTION | GET |= "feeds" | RESOURCES |= "feed" | LABEL |= "slug" | ID |= "id",
	sources 	= curator | COLLECTION | GET > "sources" | RESOURCES > ("source" | ID > "id" | LABEL > "name"),
	sources2 	= curator | COLLECTION | GET("sources") | RESOURCES("source", ID = "id", LABEL = "name") | r_.data,
)

curator.feeds.op(tempsetting1 = tempvalue).add_ops(
	posts 	= feeds | OP | COLLECTION | GET |= "feeds/{feed.id}/posts" | DRILL |= r_.posts | RESOURCES | ID |= "id",
)
"""