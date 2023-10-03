import dag
from dag import r_


catfacts = dag.cmd.GET("https://meowfacts.herokuapp.com", r_.data[0]) 


dogs = dag.cmd.GET("https://dog.ceo/api/breeds/image/random")

@dogs.display
def display_dogs(response, formatter, *, height: int = 30):
	formatter.image_from_url(response.message, maxheight = height)


breeds = dogs.collection.NO_DISPLAY.GET("https://dog.ceo/api/breeds/list/all", r_.message)