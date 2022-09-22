import os, ast
import operator as op

			

def eval_math(expression: str) -> float:
	"""
	Takes a string of a mathematical expression and evaluates it into a number

	:param expression: The string expression to evaluate
	:returns: The evaluted expression
	"""

	if isinstance(expression, (int, float)):
		return expression

	# supported operators
	operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
				 ast.Div: op.truediv, ast.Pow: op.pow,
				 ast.USub: op.neg, ast.FloorDiv: op.floordiv, ast.Mod: op.mod}
				 #ast.BitXor: op.xor, Removing xor (^) bc I confuse it with power (**)'''

	def eval_expr(expr: str) -> float:
		"""
		>>> eval_expr('2^6')
		4
		>>> eval_expr('2**6')
		64
		>>> eval_expr('1 + 2*3**(4^5) / (6 + -7)')
		-5.0
		"""
		return eval_(ast.parse(expr, mode='eval').body)

	def eval_(node: ast.expr) -> float:
		if isinstance(node, ast.Num): # <number>
			return node.n
		elif isinstance(node, ast.BinOp): # <left> <operator> <right>
			return operators[type(node.op)](eval_(node.left), eval_(node.right))
		elif isinstance(node, ast.UnaryOp): # <operator> <operand> e.g., -1
			return operators[type(node.op)](eval_(node.operand))
		else:
			raise ValueError(f"{node}, {expression=}")
			
	return eval_expr(expression)



class Convert:
	"""
	A method class for different unit conversions
	"""

	@staticmethod
	def km_to_miles(kms: float, ndigits: int = 2) -> float:
		"""
		Converts kilometers to miles

		:param kms: The number of kilometers to convert
		:param ndigits: The number of decimal places to round to
		:returns: The number of miles converted from kilometers
		"""

		return round((kms or 0)*0.621, ndigits)

	@staticmethod
	def miles_to_km(miles: float, ndigits: int = 2) -> float:
		"""
		Converts miles to kilometers

		:param kms: The number of miles to convert
		:param ndigits: The number of decimal places to round to
		:returns: The number of kilometers converted from miles
		"""

		return round(miles*1.609, ndigits = 2)

	@staticmethod
	def cels_to_far(cels_degrees: float, ndigits: int = 2) -> float:
		"""
		Converts degrees celcius to farenheit

		:param kms: The number of degrees celcius to convert
		:param ndigits: The number of decimal places to round to
		:returns: The number of degrees farenheit converted from celcius
		"""

		return round((cels_degrees * 9/5) + 32, ndigits)

	@staticmethod
	def far_to_cels(far_degrees: float, ndigits: int = 2) -> float:
		"""
		Converts degrees farenheit to celcius

		:param kms: The number of degrees farenheit to convert
		:param ndigits: The number of decimal places to round to
		:returns: The number of degrees celcius converted from farenheit
		"""

		return round((Fahrenheit - 32) * 5/9, ndigits)

	@staticmethod
	def cels_to_kel(cels_degrees: float, ndigits: int = 2) -> float:
		"""
		Converts degrees celcius to kelvin

		:param kms: The number of degrees celcius to convert
		:param ndigits: The number of decimal places to round to
		:returns: The number of degrees kelvin converted from celcius
		"""

		return round(cels_degrees + 273.15, ndigits)