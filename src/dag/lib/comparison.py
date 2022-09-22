import operator
from collections.abc import Sequence
from typing import Any, Union, Callable

# Turn symbol into operator
ops = {
	"<": operator.lt,
	"<=": operator.le,
	">": operator.gt,
	">=": operator.ge,
	#"=": operator.eq,
	"==": operator.eq,
	"!=": operator.ne,
}

# Turn operator into symbol
operators = {v:k for k,v in ops.items()}

# Turn operator name into operator function
cmp_operator_names = {v.__name__:v for k,v in ops.items()}

# A type variable for comparison operators
StoredComparison = Union["ComparisonRecorder", bool]


# A utility class that stores comparisons
class ComparisonRecorder:
	"""
	This class will store comparison checks made on it to be checked against at a later time.

	It can store multiple comparisons and check that each one passes

	eg:
		(1) cr < 2
		(2) cr < 3
		(3) cr.do_stored_comparison(1) returns True, because 1<2 AND 1<3
	"""

	def __init__(self):
		"""
		A fresh instance of the ComparisonRecorder to be compared against
		"""

		self.stored_comparisons = {}


	def is_should_record_comparison(self) -> bool:
		"""
		Indicates whether CR should be storing requested comparisons

		:returns: flag indicating whether to store comparison requests
		"""

		return True


	def store_comparison(self, comparison_name: str, val: Any) -> StoredComparison:
		"""
		If a comparison should be stored, records a comparison for future checking. Otherwise, perform the comparison

		:param comparison_name: The name of the magicmethod that performs the comparison WITHOUT the double underscores
		:param val: The value being compared against
		:returns:	(1) If the comparison should be stored: Return self for further comparisons
					(2) Else, comparison shouldn't be stored: Return the evaluation of othe comparison
		"""

		op = cmp_operator_names[comparison_name]

		if self.is_should_record_comparison():
			self.stored_comparisons.setdefault(op, []).append(val)
			return self

		bool_op = getattr(super(), f"__{comparison_name}__")
		return bool_op(val)


	def __eq__(self, val: Any) -> StoredComparison: return self.store_comparison("eq", val)	# Equals 			==
	def __ne__(self, val: Any) -> StoredComparison: return self.store_comparison("ne", val)	# Not Equals 		!=
	def __lt__(self, val: Any) -> StoredComparison: return self.store_comparison("lt", val)	# Less Than			<
	def __le__(self, val: Any) -> StoredComparison: return self.store_comparison("le", val)	# Less Than/eq 		<=
	def __gt__(self, val: Any) -> StoredComparison: return self.store_comparison("gt", val)	# Greater Than		>
	def __ge__(self, val: Any) -> StoredComparison: return self.store_comparison("ge", val)	# Greater Than/eq 	>=


	def do_stored_comparisons_against(self, comparee: Any) -> bool: 
		"""
		Compare the comparee against all stored comparisons made against CR object

		So:
			cr < 5
			cr <= 6
			cr.do_stored_comparisons_against(3) results in True

		And:
			cr < 5
			cr > 5
			cr.do_stored_comparisons_against(5) results in False


		If no comparisons have been made against CR object, return False

		:param comparee: The object being compared against
		:returns: Whether the comparee passes all comparison checks
		"""

		results = []

		for comp_op, comparer_list in self.stored_comparisons.items():
			results.append(self.do_comparison(comparee, comparer_list, comp_op))

		return all(results) if results else False


	def do_comparison(self, comparee: Any, comparer_list: Sequence[Any], comp_op: Callable[[Any, Any], bool]) -> bool:
		"""
		Performs all comparisons of a given type made against the CR object

		So:
			cr < 5
			cr < 6
			cr > 100
			cr > 200

			One call of this method will do all "<" comparisons together, then a separate call will do all ">" comparisons

		:param comparee: The object being compared against
		:param comparer_list: The list of all comparisons stored of a certain type
		:param comp_op: The comparison operation being performed
		"""

		for comparer in comparer_list:
			if not comp_op(comparee, comparer):
				return False

		return True




def sortlist(li: Sequence[Any], **kwargs) -> list[Any]:
	"""
	Provides a standardized way to sort a list of primitive python objects: None, bools, numbers, and strings

	In the returned list, the order of precedence is
		(1) None
		(2) Bools
		(3) Numbers
		(4) Strings
		(5) Any comparable objects (prone to breaking)

	:param li: The list to be sorted
	:param kwargs: Args for sorted() on string elements of li
	:returns: The sorted list
	"""

	has_none = False
	
	if None in li:
		has_none = True
		li = [i for i in li if i is not None]
		
	bools = [i for i in li if isinstance(i, bool)]
	li = [i for i in li if not isinstance(i, bool)]
		
	nums = [i for i in li if isinstance(i, (int, float))]
	li = [i for i in li if not isinstance(i, (int, float))]

	strs = [i for i in li if isinstance(i, (str))]
	li = [i for i in li if not isinstance(i, (str))]


	li = sorted(li, **kwargs)
	li = sorted(strs, **kwargs) + li
	li = sorted(nums) + li
	li = sorted(bools) + li
				
	if has_none:
		li.insert(0, None)

	return li