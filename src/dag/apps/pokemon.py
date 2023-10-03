import dag
from dag import r_


def _preformatter(formatter):
	return formatter.icstyle("Steel", "#CC", suffix="🔩").icstyle("Electric", "11", suffix="⚡").icstyle("Water", "#0FF", suffix="💦").icstyle("Fairy", "201", suffix="✨").icstyle("Grass", "#0F0", suffix="🌱").icstyle("Fire", "#F80", suffix="🔥").icstyle("Poison", "#D0D", suffix="☣").icstyle("Fighting", "#C96", suffix="👊").icstyle("Ghost", "#A0A", suffix="👻").icstyle("Flying", "#0FF", suffix="🦅").icstyle("Psychic", "magenta3").icstyle("Ice", "steelblue1", suffix="❄").icstyle("Ground", "sandybrown", suffix="🌎").icstyle("Dragon(\W|$)", "#8FF", suffix = "🐉").icstyle("Dark", "b #AA", suffix="🌙").icstyle("Bug", "darkolivegreen2", suffix="🐞").icstyle("Normal", "bold").icstyle("rock", "#C4A484", suffix="🗿")


pokeapi = dag.app.JSON("pokemon", baseurl = "http://pokeapi.co/api/v2/", preformatter = _preformatter, doc="https://pokeapi.co/docs/v2", 
		spec = "https://raw.githubusercontent.com/cliffano/pokeapi-clients/main/specification/pokeapi.yml", help = "A module for viewing information from pokemon", color="#CC0000")


pokemon = pokeapi.collection.GET("pokemon/?limit=10000", r_.results)
pokemon.resources("pokemon").label("name")


pokedex = pokemon.op(default = "magnemite").DEFAULT.CACHE.GET("pokemon/{pokemon.name}")
pokemon.default_dagcmd = pokedex


#@pokeapi.arg.Int("--height", default = 28)
#@pokeapi.arg.Flag("--unblurry", help = "If set, don't sharpen the sprite")
#@pokeapi.arg.Flag("--shiny", help = "If set, show the pokemon's shiny sprite")
@pokedex.display
def display_pokemon(response, formatter, parsed, *, height: int = 23, unblurry: bool = False, shiny: bool = False):
	sprite_url = response.sprites.front_shiny if shiny else response.sprites.front_default

	sharp = unblurry
		
	types = ", ".join([type.type.name.capitalize() for type in response.types])
	abilities =  ", ".join([ability.ability.name.capitalize() for ability in response.abilities])

	formatter = dag.img.from_url(sprite_url).to_formatter(formatter, maxheight = height, sharp = sharp)

	formatter.col(0, "bold", after = ":", margin = 2)
	formatter.add_row(f"Pokemon", response.name.capitalize(), style = "bold")
	formatter.add_row("Type(s)", types)
	formatter.add_row("Height", f"{response.height/10.0}m")
	formatter.add_row("Weight", f"{response.weight/10.0}kg")
	formatter.add_row("Abilities", abilities)


@pokeapi.cmd
def pokemonmoves(pokemon: dag.Resource[pokemon]):
	return pokedex(pokemon.name).moves


@pokemonmoves.display
def display_moves(response, formatter):
	for move in response:
		moveinfo = moves(move.move.name) # This isn't formatting @pokeapi.resources's {response.url} into the move name, so the move's GET is failing
		formatter.add_row(_format_move(moveinfo), "<c bold>Level</c>: {move.version_group_details[-1].level_learned_at}")



moves = pokeapi.collection.GET("https://pokeapi.co/api/v2/move/?limit=10000", r_.results)
moves.resources.value(dag.nab.get("{resource.url}")).label("name")



@moves.resources.display
def display_move(response, formatter):
	formatter.col(0, "bold", after = ":", margin = 2)
	
	formatter.add_row("Name", response.name.capitalize(), style = "bold")
	formatter.add_row("Effect", response.effect_entries[0].effect)
	formatter.add_row("Power", response.power)
	formatter.add_row("Type", response.type.name.capitalize())
	formatter.add_row("PP", response.pp)
	formatter.add_row("Accuracy", f"{response.accuracy}%")



	
	
abilities = pokeapi.collection("abilities").GET("ability/?limit=10000", r_.results)
abilities.resources.value(dag.nab.get("{resource.url}")).label("name")


@abilities.resources.display
def display_ability(response, formatter):
	formatter.col(0, "bold", after = ":", margin = 2)
	formatter.add_row("Name", response.name.capitalize(), style = "bold red")
	no_effect_text = "None" if response.is_main_series else "<c bold>NOTE: </c>This is not a main series ability"
	breakpoint()
	formatter.add_row("Effect", entry[0].effect if (entry := response.effect_entries({"language.name": "en"})) else no_effect_text)
	formatter.add_row("Pokemon", ", ".join([p.pokemon.name.capitalize() for p in response.pokemon]) or "None")
	formatter.add_row("Introduced", "Generation <c b>" + response.generation.url.split("/")[-2] + "</c>")



items = pokeapi.collection.GET("item/?limit=10000", r_.results)
items.resources.value(dag.nab.get("{resource.url}")).label("name")


@items.resources.display
def display_items(response, formatter):
	formatter.col(0, "bold", after = ":", margin = 2)
	formatter.add_row("Name", response.name.capitalize(), style = "bold red")
	formatter.add_row("Effect", response.effect_entries[0].effect)


@pokeapi.collection
def types():
	types = dag.get("type").results
	types_urls = [t.url for t in types]
	return dag.get(types_urls)
types.resources.label("name")	


@types.display
def display_types(response, formatter):
	formatter.ignorecase = True
	formatter.col(style = "bold", suffix = ":")
	formatter.add_row("2x Damage To", ", ".join(type.name for type in response.damage_relations.double_damage_to))
	formatter.add_row(".5 Damage To", ", ".join(type.name for type in response.damage_relations.half_damage_to), margin_bottom = 2)
	
	formatter.add_row("2x Damage From", ", ".join(type.name for type in response.damage_relations.double_damage_from))
	formatter.add_row(".5 Damage From", ", ".join(type.name for type in response.damage_relations.half_damage_from))
	


@pokeapi.cmd
def weaknesses(pokemon: dag.Resource[pokemon]):
	return pokedex(pokemon)
	

@weaknesses.display
def display_weaknesses(response, formatter):
	formatter.ignorecase = True
	
	if len(response.types) == 1:
		type = types(response.types[0].type.name)
		formatter.add_row("2x damage from", ", ".join(t.name for t in type.damage_relations.double_damage_from))
		formatter.add_row()
		formatter.add_row("1/2 damage from", ", ".join(t.name for t in type.damage_relations.half_damage_from))
		
		return
		
	type1 = types().find(response.types.filter(dag.r_.slot == 1)[0].type.name)
	type2 = types().find(response.types.filter(dag.r_.slot == 2)[0].type.name)

	t1w = set(t.name for t in type1.damage_relations.double_damage_from)
	t1r = set(t.name for t in type1.damage_relations.half_damage_from)
	t1i = set(t.name for t in type1.damage_relations.no_damage_from)
	
	t2w = set(t.name for t in type2.damage_relations.double_damage_from)
	t2r = set(t.name for t in type2.damage_relations.half_damage_from)
	t2i = set(t.name for t in type2.damage_relations.no_damage_from)

	
	formatter.col(style = "bold", suffix = ":")
	formatter.add_row("4x damage from", ", ".join((t1w & t2w)))
	formatter.add_row("2x damage from", ", ".join((t1w ^ t2w) - t2i - t2r - t1r - t1i))
	formatter.add_row()
	formatter.add_row("1/2 damage from", ", ".join((t1r ^ t2r) - t2i - t1i - t1w - t2w))
	formatter.add_row("1/4 damage from", ", ".join((t1r & t2r)))
	formatter.add_row()
	formatter.add_row("Immune to", ", ".join(t1i | t2i))