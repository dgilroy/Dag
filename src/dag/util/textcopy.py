import dag

def copy_text(text = None, echo = False, codec = "utf-8"):
	text = text.strip().strip("\n")

	response = dag.get_terminal().strip_escape_codes(text)
	response = response.replace(" "*4, "\t").replace(" "*3, "\t").replace(" "*2, "\t").replace("\t ", "\t\t")

	dag.get_platform().clipboard(response, codec)

	print("\nText Copied")
								
	if echo:
		return response