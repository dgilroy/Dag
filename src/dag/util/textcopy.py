import dag

def copy_text(text: str = None, echo: bool = False, codec: str = "utf-8") -> str:
	text = str(text)
	text = text.strip().strip("\n")

	response = dag.get_terminal().strip_escape_codes(text)
	response = response.replace(" "*4, "\t").replace(" "*3, "\t").replace(" "*2, "\t").replace("\t ", "\t\t")

	dag.get_platform().clipboard(response, codec)

	dag.echo("\nText Copied")
								
	return response