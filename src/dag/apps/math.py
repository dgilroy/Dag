import math
from statistics import mean 
import dag

math = dag.app("math")


@math.cmd()
def avg(*nums: tuple[float, ...]):
	return mean(nums)

@math.cmd("sum")
def _sum(*nums): return sum(nums)