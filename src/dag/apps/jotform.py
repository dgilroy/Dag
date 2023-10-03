import dag
from dag import r_


jotform = dag.app.JSON("jotform", baseurl = "https://api.jotform.com/", doc = "https://api.jotform.com/docs/",
			auth = dag.auth.HEADER("APIKEY", dag.nab.env.JOTFORM_TOK))

user = jotform.cmd("user").CACHE.GET("user")
usage = jotform.cmd("usage").GET("user/usage")


forms = jotform.DEFAULT.collection("forms", launch = "https://www.jotform.com/myforms/").CACHE.GET("user/forms", r_.content)
forms.resources("form").value(dag.nab.get("form/{id}")).launch("https://www.jotform.com/build/{id}").label("title").id("id")

questions = forms.op.collection("questions").GET("form/{form.id}/questions", r_.content)

submissions = forms.op.collection("submissions", launch = "https://www.jotform.com/inbox/{form.id}").GET("form/{form.id}/submissions", r_.content).filter(r_.status == "DELETED")
submissions.resources("submission").launch("https://www.jotform.com/inbox/{form_id}/{id}").id("id")