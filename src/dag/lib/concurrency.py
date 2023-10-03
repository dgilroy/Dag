from typing import Callable, List, Any
from collections.abc import Sequence

import concurrent.futures



def run_multiprocess_task(fn: Callable[..., Any], inputs: Sequence[Any], *args) -> list[Any]:
	from pathos.multiprocessing import ProcessingPool as Pool, cpu_count

	#from multiprocessing import Pool, cpu_count
	pool_count = min(len(inputs), cpu_count())

	with Pool(pool_count) as p:
		p.restart() # PATHOS provides this for if a pool is closed. It will recycle pools even if Pool() is called many times

		# amap zips the args, so each arg needs to be an array equal in length to the inputs
		try:
			return p.amap(fn, inputs, *[[a]*len(inputs) if not isinstance(a, list) else a for a in args])
		except Exception as e:
			breakpoint()
			pass
		finally:
			p.close() #PATHOS isn't properly closing pools, so have to do it myself. Hopefully pathos fixes in future: https://github.com/uqfoundation/pathos/issues/244


def run_multiprocess_get(fn: Callable[..., Any], inputs: Sequence[Any], *args) -> list[Any]:
	return run_multiprocess_task(fn, inputs, *args).get()



def multiprocess_map(fn: Callable[..., Any], inputs: Sequence[Any], *args) -> list[Any]:
	"""
	Initiates a multiprocessing mapping. Calls the fn once for each provided input.
	Any provided *args are passed into all mappings. Each mapping uses the same args

	If only one input is received, call the function like normal and return in a list

	Results are returned in order of inputs received

	:param fn: The function to be called multiple times
	:param inputs: The inputs to be passed, one at a time, into a mapping
	:param args: Any args that must be passed into every maping
	:returns: A list of the results after each mapping has completed
	"""

	# If more than one input: Initiate multiprocessing and run each input
	if len(inputs) > 1:
		return run_multiprocess_get(fn, inputs, *args)

	# Else, only one input: Run the input and return its value in a list
	return [fn(inputs[0], *args)]


def multithread_map(fn: Callable[..., Any], inputs: Sequence[Any], *args) -> list[Any]:
	"""
	Initiates a multithread mapping. Calls the fn once for each provided input.
	Any provided *args are passed into all mappings. Each mapping uses the same args

	If only one input is received, call the function like normal and return in a list

	Results are returned in order of inputs received

	:param fn: The function to be called multiple times
	:param inputs: The inputs to be passed, one at a time, into a mapping
	:param args: Any args that must be passed into every maping
	:returns: A list of the results after each mapping has completed
	"""

	# If input is an array, run in threads
	if len(inputs) > 1:
		# We can use a with statement to ensure threads are cleaned up promptly
		with concurrent.futures.ThreadPoolExecutor() as executor:
			# map
			return list(executor.map(fn, inputs, *[[a]*len(inputs) for a in args]))

	# Else, only single input: run normally 	
	return [fn(inputs[0], *args)]




"""
def async_process_data(data):
    '''Simulate processing of data.'''
    loop = asyncio.get_event_loop()
    tasks = []
    for d in data:
        tasks.append(loop.run_in_executor(None, process_data, d))
    loop.run_until_complete(asyncio.wait(tasks))
    return True
"""