import dag
from dag import this



@dag.mod("pokemon", baseurl = "http://pokeapi.co/api/v2/", preformatter = this._preformatter, default_cmd = this.pokedex, doc="https://pokeapi.co/docs/v2", 
		spec = "https://raw.githubusercontent.com/cliffano/pokeapi-clients/main/specification/pokeapi.yml", response_parser = dag.JSON)
class Pokemon(dag.DagMod):
	"""A module for viewing information from pokemon"""

	def _preformatter(self, formatter):
		return formatter.cstyle("Steel", "#CC", suffix="🔩").cstyle("Electric", "11", suffix="⚡").cstyle("Water", "#0FF", suffix="💦").cstyle("Fairy", "201", suffix="✨").cstyle("Grass", "#0F0", suffix="🌱").cstyle("Fire", "#F80", suffix="🔥").cstyle("Poison", "#D0D", suffix="☣").cstyle("Fighting", "#C96", suffix="👊").cstyle("Ghost", "#A0A", suffix="👻").cstyle("Flying", "#0FF", suffix="🦅").cstyle("Psychic", "magenta3").cstyle("Ice", "steelblue1", suffix="❄").cstyle("Ground", "sandybrown", suffix="🌎").cstyle("Dragon(\W|$)", "#8FF", suffix = "🐉").cstyle("Dark", "b #AA", suffix="🌙").cstyle("Bug", "darkolivegreen2", suffix="🐞").cstyle("Normal", "bold")


	#@dag.resources(value = dag.nab.get("{resource.url}"), display = this._display_pokemon)
	# ^ Not implementing resource, have no way to pass arguments like "shiny" and then get resource
	@dag.resources(label = "name")
	@dag.collection(value = dag.nab.get("pokemon/?limit=10000").results)
	def pokemon(self):
		return


	@dag.arg("--unsharp", flag = True, help = "If True, show the pokemon's unsharp sprite", cacheable = False)
	@dag.arg("--shiny", flag = True, help = "If True, show the pokemon's shiny sprite", cacheable = False)
	@pokemon("pokemon")
	@dag.cmd( value = dag.nab.get("pokemon/{pokemon.name}"), cache = True, display = this._display_pokemon )
	def pokedex(self, pokemon = "magnemite", shiny = False, unsharp = False):
		return		

		
	def _display_pokemon(self, response, formatter, parsed):
		sprite_url = response.sprites.front_shiny if parsed.get("shiny") else response.sprites.front_default

		sharp = not parsed.get("unsharp")
			
		types = ", ".join([type.type.name.capitalize() for type in response.types])
		abilities =  ", ".join([ability.ability.name.capitalize() for ability in response.abilities])

		formatter = dag.img.from_url(sprite_url).to_formatter(formatter, maxheight = 24, sharp = sharp)

		formatter.col(0, "bold", after = ":", margin = 2)
		formatter.add_row(f"Pokemon", response.name.capitalize(), style = "bold")
		formatter.add_row("Type(s)", types)
		formatter.add_row("Height", f"{response.height/10.0}m")
		formatter.add_row("Weight", f"{response.weight/10.0}kg")
		formatter.add_row("Abilities", abilities)


	@pokemon("pokemon", drill = "name")
	@dag.cmd(value = this.pokedex(dag.arg("pokemon").name).moves, display = this._display_moves)
	def pokemonmoves(self, pokemon):
		return


	def _display_moves(self, response, formatter):
		for move in response:
			moveinfo = self.moves(move.move.name) # This isn't formatting @dag.resources's {response.url} into the move name, so the move's GET is failing
			formatter.add_row(self._format_move(moveinfo), "<c bold>Level</c>: {move.version_group_details[-1].level_learned_at}")


	def _display_move(self, response, formatter):
		formatter.col(0, "bold", after = ":", margin = 2)
		
		formatter.add_row("Name", response.name.capitalize(), style = "bold")
		formatter.add_row("Effect", response.effect_entries[0].effect)
		formatter.add_row("Power", response.power)
		formatter.add_row("Type", response.type.name.capitalize())
		formatter.add_row("PP", response.pp)
		formatter.add_row("Accuracy", f"{response.accuracy}%")

	
	@dag.resources(value = dag.nab.get("{resource.url}"), display = this._display_move, label = "name")
	@dag.collection(value = dag.nab.get("https://pokeapi.co/api/v2/move/?limit=10000").results)
	def moves(self):
		return
		
		
	@dag.resources(value = dag.nab.get("{resource.url}"), display = this._display_ability, label = "name")
	@dag.collection(value = dag.nab.get("ability/?limit=10000").results)
	def ability(self):
		return

	
	def _display_ability(self, response, formatter):
		formatter.col(0, "bold", after = ":", margin = 2)
		formatter.add_row("Name", response.name.capitalize(), style = "bold red")
		no_effect_text = "None" if response.is_main_series else "<c bold>NOTE: </c>This is not a main series ability"
		breakpoint()
		formatter.add_row("Effect", entry[0].effect if (entry := response.effect_entries({"language.name": "en"})) else no_effect_text)
		formatter.add_row("Pokemon", ", ".join([p.pokemon.name.capitalize() for p in response.pokemon]) or "None")
		formatter.add_row("Introduced", "Generation <c b>" + response.generation.url.split("/")[-2] + "</c>")


	@dag.resources(value = dag.nab.get("{resource.url}"), display = this._display_items, label = "name")
	@dag.collection(value = dag.nab.get("item/?limit=10000").results)
	def items(self):
		return
	

	def _display_items(self, response, formatter):
		formatter.col(0, "bold", after = ":", margin = 2)
		formatter.add_row("Name", response.name.capitalize(), style = "bold red")
		formatter.add_row("Effect", response.effect_entries[0].effect)


	@dag.arg.Resource("resource", collection = [this.items, this.ability])
	@dag.cmd(value = dag.arg("resource"))
	def test(self, resource):
		return
		
	
	@dag.resources(label = "name")	
	@dag.collection(display = this._display_types)
	def types(self):
		types = dag.get("type").results
		types_urls = [t.url for t in types]
		return dag.get(types_urls)


	def _display_types(self, response, formatter):
		formatter.ignorecase = True
		formatter.col(style = "bold", suffix = ":")
		formatter.add_row("2x Damage To", ", ".join(type.name for type in response.damage_relations.double_damage_to))
		formatter.add_row(".5 Damage To", ", ".join(type.name for type in response.damage_relations.half_damage_to), margin_bottom = 2)
		
		formatter.add_row("2x Damage From", ", ".join(type.name for type in response.damage_relations.double_damage_from))
		formatter.add_row(".5 Damage From", ", ".join(type.name for type in response.damage_relations.half_damage_from))
		

	@pokemon("pokemon")
	@dag.cmd(value = this.pokedex(dag.arg("pokemon")), display = this._display_weaknesses)
	def weaknesses(self, pokemon):
		return
		

	def _display_weaknesses(self, response, formatter):
		formatter.ignorecase = True
		
		if len(response.types) == 1:
			type = self.types(response.types[0].type.name)
			formatter.add_row("2x damage from", ", ".join(t.name for t in type.damage_relations.double_damage_from))
			formatter.add_row()
			formatter.add_row("1/2 damage from", ", ".join(t.name for t in type.damage_relations.half_damage_from))
			
			return
			
		type1 = self.types(response.types({"slot": 1})[0].type.name)
		type2 = self.types(response.types({"slot": 2})[0].type.name)
		
		t12xw = set(set(t.name for t in type1.damage_relations.double_damage_from))
		t1hxw = set(set(t.name for t in type1.damage_relations.half_damage_from))
		t10xw = set(set(t.name for t in type1.damage_relations.no_damage_from))
		
		t22xw = set(set(t.name for t in type2.damage_relations.double_damage_from))
		t2hxw = set(set(t.name for t in type2.damage_relations.half_damage_from))
		t20xw = set(set(t.name for t in type2.damage_relations.no_damage_from))
		
		formatter.col(style = "bold", suffix = ":")
		formatter.add_row("4x damage from", ", ".join(t12xw.intersection(t22xw) - t20xw))
		formatter.add_row("2x damage from", ", ".join(t12xw.symmetric_difference(t22xw) - t20xw))
		formatter.add_row()
		formatter.add_row("1/2 damage from", ", ".join(t1hxw.symmetric_difference(t2hxw) - t20xw))
		formatter.add_row("1/4 damage from", ", ".join(t1hxw.intersection(t2hxw) - t20xw))
		formatter.add_row()
		formatter.add_row("Immune to:", ", ".join(t10xw.union(t20xw)))