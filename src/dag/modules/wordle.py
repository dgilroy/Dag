import string, enum

import dag
from dag import this



@dag.mod("wordle", baseurl = "https://v1.wordle.k2bd.dev/", help = "Play a clone of Worlde", default_cmd = this.play_daily, doc = "https://v1.wordle.k2bd.dev/redoc",
			spec = "https://v1.wordle.k2bd.dev/openapi.json", response_parser = dag.JSON)
class WordleClone(dag.DagMod):
	# Results Enum
	class Result(enum.Enum):
		EMPTY = -1
		ABSENT = 0
		PRESENT = 1
		CORRECT = 2


	# Results ctag styles
	resultformat = {
		Result.EMPTY.name: "",
		Result.ABSENT.name: "bg-#38",
		Result.PRESENT.name: "bg-#b59f3b black",
		Result.CORRECT.name: "bg-#538d4e"
	}



	@dag.arg("size", type = int)
	@dag.arg("word")
	@dag.resources(id = "guess")
	@dag.collection(value = dag.nab.get("daily?guess={word}&size={size}"))
	def guess(self, word, size = 5):
		return

	
	@dag.arg("--size", type = int)
	@dag.arg("word")
	@dag.cmd()
	def play_daily(self, word = "", size = 5):
		results = []

		resultchars = {char: self.Result.EMPTY for char in string.ascii_lowercase}

		while True:
			guess = word or input("Guess > ")

			if guess == "":
				break

			if guess == "bb":
				breakpoint()

			if len(guess) != size:
				print(f"Guess must be {size} letters long")
				continue

			# Get result
			result = self.guess(guess, size)
			# Store result
			results.append(result)

			# Print all stored results
			dag.echo("\n")
			[dag.echo(self._display_guess(r)) for r in results]

			# Reset guess
			guess = word = None

			# If word is correct, end session
			if result.all(lambda r: r.result == "correct"):
				return

			if len(results) >= 2:
				breakpoint(0)
				pass

			for letterresult in result:
				currentcharresult = resultchars.get(letterresult.guess)
				currentletterresult = getattr(self.Result, letterresult.result.upper())

				if currentletterresult.value > currentcharresult.value:
					resultchars[letterresult.guess] = currentletterresult

			result_string = "\n\n"
			for letter, result in resultchars.items():
				ctag_style = self.resultformat[result.name]
				result_string += f"<c {ctag_style}> {letter} </c>"

			dag.echo(result_string + "\n")

	
	def _display_guess(self, response):
		text = ""

		for guess_letter in response:
			text += f"<c b {self.resultformat[guess_letter.result.upper()]}> {guess_letter.guess} </c>"

		return text