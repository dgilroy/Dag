import re, copy, math, shutil, textwrap, unicodedata, contextlib

from collections import defaultdict
from collections.abc import MutableSequence, MutableMapping
from typing import Self

import dag
from dag.util import ctags



class Column(MutableMapping, dag.dot.DotAccess):
	default_style = {
		"title": "",
		"style": "",
		"margin": 3,
		"prefix": "",
		"before": "",
		"after": "",
		"suffix": "",
		"width": None,
		"flex": False,
		"just": str.ljust,
		"max_width": shutil.get_terminal_size().columns,
		"greedy": True,
	}

	def __init__(self, incmd = None, **settings):
		self.settings = settings

		self.default_style["max_width"] = shutil.get_terminal_size().columns

	def __getattr__(self, setting, default = None):	return (self.default_style | self.settings).get(setting, default)
	def __getitem__(self, setting): return self.settings[setting]
	def __setitem__(self, setting, value): self.settings[setting] = value
	def __delitem__(self, setting): del self.settings[setting]
	def __iter__(self):	return iter(self.settings)
	def __len__(self): return len(self.settings)
			
	def __repr__(self):
		return f"<{object.__repr__(self)} -> {self.settings}"
		
	def copy(self):
		return self.__class__(**self.settings)

	def col_settings(self):
		return self.default_style | self.settings

		
		
		
class Row(MutableSequence, dag.dot.DotAccess):
	def __init__(self, formatter, contents = [], item = None, idxitem = None, templistname = None, templistitem = None, **settings):
		self.contents = contents
	
		self.settings = settings
		self.formatter = formatter
		self.item = item 					# Any object that might be associated with this row
		self.idxitem = idxitem 				# Any numerically-indexed object that might be associated with this row (e.g. used by alists)
		self.templistname = templistname
		self.templistitem = templistitem 	# Any object that might be associated with this row (used by templists)
		
		self.settings.setdefault("style", "")
		self.settings.setdefault("margin_top", 0)
		self.settings.setdefault("margin_bottom", 1)
		self.settings.setdefault("is_message", False)
		self.settings.setdefault("padding_left", 0)
		self.settings.setdefault("id", None)
		self.settings.setdefault("enumerable", True)
		self.settings.setdefault("enum", True)
		self.settings.setdefault("just", str.ljust)

		self.cellstyles = defaultdict(Column)
		
		self.ansiiesc = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
		self.re_ctag = re.compile(r'</?c.*?>')
		
		for i in (self.id or "").split() or [None]:
			self.cellstyles.update({colidx: col.copy() for colidx, col in self.formatter.cols.get(i, {}).items()})

		self.cells = [self.generate_cell(content, idx) for idx, content in enumerate(contents)]

		


	class Cell:
		def __init__(self, row, content = None, idx = None):
			self.row = row
			self.idx = idx
			self.content = str(content)

			
		@property
		def contents(self):
			return [self.content, self.style.suffix + self.style.before, self.style.after + self.style.suffix]

		@property
		def content(self):
			return self._content

			
		@content.setter
		def content(self, content = ""):
			self._content = content
			self.unformatted_content = self.get_unformatted_content(content)
			
			
		def unformatted_content_length(self):
			return len(self.unformatted_content) + self.emoji_length()
			
			
		def unformatted_length(self):
			return sum(map(self.get_unformatted_content_length, self.contents))
			
			
		def get_unformatted_content_length(self, text):
			return len(self.get_unformatted_content(text))
			

		def get_unformatted_content(self, text):
			return re.sub("</?c.*?>", "", text)
			
			
		def emoji_length(self):
			return sum(map(self.get_emoji_length, self.contents))
			
		
		def get_emoji_length(self, text):
			return sum(1 for _ in filter(lambda x: x != "█" and unicodedata.category(x) == "So", text))


		def ansii_length(self):
			return sum(map(self.get_ansii_length, self.contents))
			
			
		def get_ansii_length(self, text):
			ansiistyles = self.row.ansiiesc.findall(text)
			return sum(map(len, ansiistyles))
			
			
		def ctag_length(self):
			return sum(map(self.get_ctag_length, self.contents))
			
			
		def get_ctag_length(self, text):
			ctags = self.row.re_ctag.findall(text)
			return sum(map(len, ctags))


		@property
		def width(self):
			return self.style.width or self.style.margin


		@property
		def text_width(self):
			try:
				return self.width - self.style.margin - (self.row.padding_left if self.cellidx == 0 else 0)
			except Exception as e:
				breakpoint()
				pass
		
		
		def is_empty(self):
			return bool(self.content)
		
		
		@property
		def cellidx(self):
			return self.row.cells.index(self)

			
		@property
		def style(self):
			negative_style = self.row.cellstyles.get(self.cellidx - len(self.row), {})
			positive_style = self.row.cellstyles.get(self.cellidx, self.row.formatter.default_col)

			style_str = ""

			if positive_style.get("style", "") or negative_style.get("style", ""): # This prevents the style_str from turning into " ", breaking some later bool checks
				style_str = positive_style.get("style", "") + " " + negative_style.get("style", "")

			style = dag.DotDict({**Column.default_style, **positive_style, **negative_style})

			style["style"] = style_str
			return style

			
		def __str__(self):
			return str(self.content)
			
			
		def __repr__(self):
			return f"<{object.__repr__(self)} -> content: {self.content}, style: {self.style}"
			
				
	def generate_cell(self, content, idx):
		return self.Cell(self, content, idx)
		
	
	def __repr__(self):
		return f"<{object.__repr__(self)} -> Cells:\n\n{self.cells}>\n\nSettings:\n\n{self.settings}"
	
	
	def __getattr__(self, setting, default = None):	return self.settings.get(setting, default)

	# Implement abstract class w/ these methods
	def __getitem__(self, cellidx):	return self.cells[cellidx]
	def __setitem__(self, cellidx, content): self.cells[cellidx] = self.generate_cell(content, cellidx)
	def __delitem__(self, cellidx):	del self.cells[cellidx]
	def __len__(self): return len(self.cells)

	
	def create_cells_at_idx(self, cellidx):
		if cellidx >= len(self.cells):
			for cellidx in range(len(self.cells), cellidx + 1):
				self.cells.append(self.generate_cell("", cellidx))
				
				
	def is_empty(self, pdb = False):
		return not any([cell.content for cell in self.cells])

				
	def set_cell(self, cellidx, content):
		self.create_cells_at_idx(cellidx)					
		self.cells[cellidx].content = content

		
	def prepend_cell(self, cellidx, content):
		self.create_cells_at_idx(cellidx)	
		cell_content = self.cells[cellidx].content
		self.cells[cellidx].content = content + cell_content
		
		
	def insert(self, cellidx, content):
		self.cells.insert(cellidx, self.generate_cell(content, cellidx))

		
	def clear_cells(self):
		for cell in self.cells:
			cell.content = ""


	def setall_cellstyles(self, style, value):
		for styleidx, cellstyle in self.cellstyles.items():
			cellstyle[style] = value
			
			
	def copy_cellstyles(self):
		return {idx: style.copy() for idx, style in self.cellstyles.items()}



#>>>> Item Iterator
class ItemIterator:
	def __init__(self, items, formatter):
		self.itemslist = iter(items) # Done this way in case the "items" is already an iterator
		self.formatter = formatter
		self.oldactiveitem = self.formatter.activeitem
		self.idx = 0

	def __iter__(self):
		return self

	def __next__(self):
		try:
			item = next(self.itemslist)
			self.formatter.activate_item(item)
			self.idx += 1
			return item
		except:
			self.formatter.activeitem = self.oldactiveitem
			raise StopIteration
#<<<< Item Iterator


#>>>> Idx Item Iterator
class IdxItemIterator:
	def __init__(self, items, formatter):
		self.itemslist = iter(items) # Done this way in case the "items" is already an iterator
		self.formatter = formatter
		self.oldactiveidxitem = self.formatter.activeidxitem
		self.idx = 0

	def __iter__(self):
		return self

	def __next__(self):
		try:
			item = next(self.itemslist)
			self.formatter.activate_idxitem(item)
			self.idx += 1
			return item
		except:
			self.formatter.activeidxitem = self.oldactiveidxitem
			raise StopIteration
#<<<< Idx Item Iterator


#### DAG FORMATTER #####

class DagStyleFormatter:	
	COL_MARGIN_DEFAULT = 3
		
	#class DagStyleFormatter
	def __init__(self, ic_response = None):
		self.ic_response = ic_response
		self.data = []
		self.rows = []
		
		self.ignorecase = False
		
		self.default_col = Column()
		
		self.colcount = 0
		self.cols = {}
		
		self.repl = {}
		self.rowstyles = {}

		self.itemslist = []			# Maintains the order of items as presented within the formatted response
		self.activeitem = None
		self.totalitems = 0


		self.idxitemslist = []		# Maintains the order of indexed items as presented within the formatted response
		self.activeidxitem = None
		self.totalidxitems = 0

		self.templist = []
		self.activetemplistitem = None


	def activate_item(self, item):
		self.activeitem = item
		self.totalitems += 1


	def activate_idxitem(self, item):
		self.activate_item(item)
		self.activeidxitem = item
		self.totalidxitems += 1


	@contextlib.contextmanager
	def idxitem(self, item):
		try:
			oldidxitem = self.activeidxitem
			self.activate_idxitem(item)
			yield item
		finally:
			self.activeidxitem = oldidxitem


	@contextlib.contextmanager
	def item(self, item):
		try:
			olditem = self.activeitem
			self.activate_item(item)
			yield item
		finally:
			self.activeitem = olditem


	def image_from_url(self, url, *args, **kwargs):
		img = dag.img.from_url(url)
		img.to_formatter(self, *args, **kwargs)



	@contextlib.contextmanager
	def templistitem(self, item, templist):
		try:
			oldtemplistitem = self.activetemplistitem
			self.templist  = templist
			self.activetemplistitem = item
			yield item
		finally:
			self.activetemplistitem = oldtemplistitem



	def idxitems(self, items):
		yield from IdxItemIterator(items, self)


	def items(self, items):
		yield from ItemIterator(items, self)

		

	def col(self, colidx = None, *style, id = None, **settings) -> Self:
		if colidx is None:
			colidx = max(self.cols.get(id, {}).keys(), default = -1) + 1

		self.cols.setdefault(id, {})
			
		col = Column()			
		col.update(self.cols.get(None, {}).get(colidx, {}))
		col.update(self.cols[id].get(colidx, {}))
		col.update(settings)
		
		if id == None:
			self.cols[id][colidx] = col
		else:
			for i in (id or "").split():
				self.cols[i][colidx] = col
		
		if style:
			col.settings['style'] = col.settings.get("style", "") + " " + " ".join(str(i) for i in style)
	
		return self
		

	@property
	def rows_by_id(self) -> dict[str, Row]:
		rows_by_id = {}

		for row in self.rows:
			rows_by_id.setdefault(row.id, []).append(row)
			
		return rows_by_id

	
	def copy_colstate(self, id: str | None = None) -> dict[int, Column]:
		return {colidx: copy.deepcopy(col) for colidx, col in self.cols.get(id, {}).items()}


	def generate_row(self, *contents, **rowinfo) -> Row:
		return Row(self, contents, item = self.activeitem, idxitem = self.activeidxitem, templistitem = self.activetemplistitem, **rowinfo)


	def copy_row(self, row, blank: bool = False) -> Row:
		contents = row.cells if not blank else []
		return self.generate_row(*contents, style = row.style, margin_bottom = row.margin_bottom, margin_top = row.margin_top, is_message = row.is_message, id = row.id)


	def add_row(self, *contents, **rowinfo) -> Self:
		self.rows.append(self.generate_row(*contents, **rowinfo))
		return self


	def add_titles(self, id = None) -> Self:
		title_row = [col.title for col in self.cols.get(None, {}).values()]

		if any(title_row):
			self.rows.insert(0, self.generate_row(*title_row, style = "bold red", id = id, is_title = True, ignore_colstyle = True, enumerable = False))

		return self


	def add_message(self, *contents, style = "bold", margin_bottom = 2) -> Self:
		self.add_row(*contents, style = style, margin_bottom = margin_bottom, is_message = True, id ="__message__", enumerable = False)
		return self


	def sub(self, pattern, repl, ignorecase = False) -> Self:
		ignorecase = re.IGNORECASE if (ignorecase or self.ignorecase) else 0
		self.repl[re.compile("(" + pattern + ")", ignorecase)] = repl
		return self
		
		
	def cstyle(self, pattern: str, style: str, prefix: str = "", suffix: str = "", ignorecase: bool = False, rowstyle: str = "") -> Self:
		ignorecase = re.IGNORECASE if (ignorecase or self.ignorecase) else 0
		repattern = re.compile("(" + pattern + ")", ignorecase)
		self.repl[repattern] = rf"<c {style}>{prefix}\1{suffix}</c {style}>"

		if rowstyle:
			self.rowstyles[repattern] = rowstyle

		return self


	def icstyle(self, *args, **kwargs) -> Self:
		return self.cstyle(*args, ignorecase = True, **kwargs)


	def insert_column(self, colidx: int, column: Column) -> None:
		cols = {}
		for colstyleid, colstyles in self.cols.items():
			cols.setdefault(colstyleid, {})
			cols[colstyleid] = {key + 1: col for key, col in colstyles.items() if key >= colidx}
			cols[colstyleid][colidx] = column.copy()
			cols[colstyleid][colidx].settings['id'] = colstyleid

		self.cols = cols
		
		for row in self.rows:
			row.cellstyles.update({key + 1: cellstyle for key, cellstyle in row.cellstyles.items() if key >= colidx})
			row.cellstyles[colidx] = (cols.get(row.id) and cols[row.id][colidx]) or column.copy()


	def _enumerate_rows_from_itemtype(self, itemtype: str, colidx: int, itemslist: list[object] | None = None) -> None:
		rowidx = 0

		self.insert_column(colidx, Column(margin = 2, style = "#E7FD39"))

		activeitem = None

		for row in self.rows:
			if row.is_message:
				continue

			row.insert(colidx, "")

			if getattr(row, itemtype) != activeitem:
				activeitem = getattr(row, itemtype)

				# If new item is just None: don't enumerate
				if activeitem is not None:
					if itemslist is not None:
						itemslist.append(activeitem) # May be used in future for when alist collection differs from input collection

					row[colidx].content = f"{rowidx}:"
					rowidx += 1


	def maybe_enumerate_rows(self, colidx: int = 0) -> None:	
		if self.totalidxitems:
			self._enumerate_rows_from_itemtype("idxitem", colidx = colidx, itemslist = self.idxitemslist)
			
		if self.templist:
			self._enumerate_rows_from_itemtype("templistitem", colidx = colidx)

					
	def set_col_lens(self) -> None:
		collens = {}

		for row in self.rows:
			collens.setdefault(row.id, {})

			for cellidx, cell in enumerate(row):
				if row.is_message:
					continue

				for pattern, repl in self.repl.items():
					if pattern.search(cell.content):
						cell.content = pattern.sub(repl, cell.content)
						row.settings['style'] = self.rowstyles.get(pattern, "") + " " + row.settings.get('style' "")

				collens[row.id][cellidx] = min(cell.style.max_width, max(collens[row.id].get(cellidx, 0), cell.unformatted_length() + cell.emoji_length() + cell.style.margin + (row.padding_left if cellidx == 0 else 0)))
				breakpoint(collens[row.id][cellidx] < 0)

		self.content_collens = collens
		window_width = shutil.get_terminal_size().columns

		for rowid, total_collen in collens.items():
			max_len_per_cell = math.floor(window_width / max(1, len(collens[rowid])))
			
			undersized_cells = 0
			for colidx, collen in collens[rowid].items():
				if collen < max_len_per_cell:
					undersized_cells = undersized_cells + 1
					max_len_per_cell += (max_len_per_cell - collen)/max(1, len(collens[rowid]) - undersized_cells)
					
			max_len_per_cell = math.floor(max_len_per_cell)
					
			for colidx, collen in collens[rowid].items():
				collens[rowid][colidx] = min(collen, max_len_per_cell, row.cellstyles[colidx].max_width)
				breakpoint(collens[rowid][colidx] < 0)

			for row in self.rows:
				for cellidx, cell in enumerate(row.cells):
					row.cellstyles.setdefault(cellidx, Column())

				for colidx, cellstyle in row.cellstyles.items():
					if collens[row.id].get(colidx):
						cellstyle.settings["width"] = collens[row.id][colidx] if not row.id == "__message__" else window_width
						
						
	def generate_overflow_row(self, row: Row) -> Row:
		overflow_row = self.generate_row(id = row.id, style = row.style)
		overflow_row.cellstyles = row.copy_cellstyles()
		overflow_row.create_cells_at_idx(len(row.cells) - 1)
		overflow_row.setall_cellstyles("after", "")
		overflow_row.setall_cellstyles("suffix", "")
		overflow_row.setall_cellstyles("before", "")
		overflow_row.padding_left = row.padding_left
		return overflow_row


	def print_message(self, row: Row) -> str:
		rowstyle_openctag = ""
		rowstyle_closectag = ""

		if row.style:
			rowstyle_openctag = f"<c {row.style}>"
			rowstyle_closectag = "</c>"

		if self.ic_response:
			self.ic_response.response_no_multicol += "\n"*row.margin_top + rowstyle_openctag + row.cells[0].content + rowstyle_closectag +"\n"*row.margin_bottom

		return "\n"*row.margin_top + rowstyle_openctag + row.cells[0].content.ljust(row.cells[0].style.max_width - 5) + rowstyle_closectag +"\n"*row.margin_bottom


	def print_row(self, row: Row, is_overflow_row: bool = False) -> str:
		if row.is_message:
			return self.print_message(row)			

		response_str = ""

		rowstyle = f"<c {row.style}>" if row.style else ""

		overflow_row = self.generate_overflow_row(row)
		
		for cellidx, cell in enumerate(row.cells):
			left_padding = " "*(row.padding_left if cellidx == 0 else 0)

			cellstyle = cell.style if not row.ignore_colstyle else ""

			columnstyle = self.cols.get(row.id, {}).get(cellidx, {}).get("style", "")
			opencolumnstyle = "<c {columnstyle}>" if columnstyle else ""
			closeolumnstyle = "</c {columnstyle}>" if columnstyle else ""

			colstyle = f"<c {cellstyle.style}>" if (cellstyle and cellstyle.style and not cellstyle.style == row.cellstyles.get(cellidx-1, self.generate_row()).style) else ""
			colclosetag = f"</c {cellstyle.style}>" if (cellstyle and cellstyle.style and not cellstyle.style == row.cellstyles.get(cellidx+1, self.generate_row()).style) else ""
			
			after = cellstyle.after + cellstyle.suffix if cellstyle else ""
			before = cellstyle.prefix + cellstyle.before if cellstyle else ""
			margin = cellstyle.margin if cellstyle else self.COL_MARGIN_DEFAULT
						
			rowclosetag = f"</c>" if row.style else ""
			
			if not is_overflow_row:
				try:
					total_ljust = max(max(len(cell.content), self.content_collens[row.id].get(cellidx, 0)) + len(after) + len(before) + margin - (row.padding_left if cellidx == 0 else 0), cell.width)

				except Exception as e:
					breakpoint()
					pass
				
				if self.ic_response:
					self.ic_response.response_no_multicol += f"{left_padding}{before}{cell.content}{after}".ljust(total_ljust)
				
			if "\n" in cell.content:
				split_lines = cell.content.split("\n")
				overflow_row.set_cell(cellidx, "\n".join(split_lines[1:]))
				cell.content = split_lines[0] + "\n"

			if cell.text_width and cell.unformatted_content_length() > cell.text_width:
				newline = ""
				if re.search(r"\n*$", cell.content):
					newline = re.search(r"\n*$", cell.content)[0]

				textwidth = max(cell.text_width, 2)
				#line_content = textwrap.wrap(cell.content, width = textwidth) or ['']
				line_content = ctags.CTagWordWrapper(textwidth).wrap(cell.content) or ['']
				with dag.catch() as e:
					line_content[-1] += newline

				overflow_row.prepend_cell(cellidx , " ".join(line_content[1:]))
				cell.content = line_content[0]

			response_str += "\n"*row.margin_top + f"{rowstyle}{colstyle}" + cell.style.just(f"{left_padding}{before}{cell.content}{after}", (cell.width + cell.ctag_length() - cell.emoji_length() - cell.style.margin)) + f"{colclosetag}" + " "*cell.style.margin + f"{rowclosetag}"

		if not overflow_row.is_empty():
			response_str += "\n"
			response_str += self.print_row(overflow_row, is_overflow_row = True)

		if not is_overflow_row:
			response_str += "\n"*(row.margin_bottom if overflow_row.is_empty() else max(2, row.margin_bottom))
			if self.ic_response:
				self.ic_response.response_no_multicol += "\n"*(row.margin_bottom)

		return response_str
		
		
	def print_response(self):
		response_str = ""
		
		self.add_titles()

		self.maybe_enumerate_rows()
				
		self.set_col_lens()

		for rowidx, row in enumerate(self.rows):
			response_row = self.print_row(row)
			#print(response_row)
			response_str += response_row
				
		return response_str
		

	def __str__(self):
		return self.print_response()