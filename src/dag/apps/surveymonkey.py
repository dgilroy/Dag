import dag



sm = dag.app.JSON("surveymonkey", baseurl = "https://api.surveymonkey.com/v3/", auth = dag.auth.OAUTH(dag.nab.env.SURVEYMONKEY_TOK), 
	doc = "https://developer.surveymonkey.com/api/v3/#SurveyMonkey-Api")


me = sm.cmd.GET("users/me")

#surveys = sm.collection.DEFAULT("surveys").GET("surveys").data

@sm.DEFAULT.collection(value = dag.nab.get("surveys").data)
def surveys():
	pass
surveys.resources("survey").label("title")


@surveys.resources.launch
def launch_survey(survey):
	surveyinfo = dag.get(survey.href)
	return surveyinfo.summary_url


@surveys.op(value = dag.nab.get("surveys/{survey.id}/responses").total)
def total_results(survey):
	pass

