from collections.abc import Sequence

def is_nonstring_sequence(item: object):
	return isinstance(item, Sequence) and not isinstance(item, str)


def listify(item: object, iterclass: type = None, stripnone = False):
	origiterclass, iterclass = iterclass, iterclass or list

	if not is_nonstring_sequence(item):
		item = iterclass([item]) # Done this way because iterclass(non-list) doesn't work (e.g. tuple(None))
	else:
		item = iterclass(item) if origiterclass else item

	if stripnone:
		return nonefilter(item)

	return item


# If a list only has one item, return only that entry. Otherwise, return the list
def unlistify(item: object) -> object:
	if not is_nonstring_sequence(item):
		return item

	if len(item) == 1:
		return item[0]

	return item


def nonefilter(item) -> list[object]:
	return [i for i in item if i is not None]


def flattenlist(lst) -> list:
	response = []

	for i in lst:
		if not is_nonstring_sequence(i):
			response.append(i)
		else:
			response.extend(i)

	return response