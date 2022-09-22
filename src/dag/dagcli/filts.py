from dag.lib import comparison

def filter(collection, incmd):
	for key, vals in incmd.filts["filter"].items():
		action = lambda **filters: collection.filter(_dag_use_str = True, **filters)
		if vals[0] in comparison.ops:
			op = vals[0] # Preserves value for lambda

			if op == "=":
				op = "=="

			action = lambda x: collection.compare(id = x, op = op)
			vals.pop(0)

		items = collection.create_subcollection()

		for val in vals:
			val = val[1:] if val and val[0] in ["'", '"'] else val # Strip quotes
			val = val[:-1] if val and val[-1] in ["'", '"'] else val # Strip quotes

			if val.startswith("r/") and val.endswith("/"):
				val = val[2:-1]
				action = lambda **filters: collection.filter_regex(**filters)

			items += action(**{key: val})

		collection = items
		
	for p in incmd.filts["partition"]:
		collection = collection.partition(p)
		collection.sort_by_keys()
		
	if collection.total_resoures() == 1:
		collection = collection[0]		# Done so that I can do things like =p or > if a single item is returned

	return collection
