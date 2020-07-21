import sublime, sublime_plugin
import re
from .utils import *
from . import CleverInsert as ci

class CleverPasteCommand(sublime_plugin.TextCommand):
	def __init__(self, view):
		super().__init__(view)
		self.view = view
		self.current_syntax = get_current_syntax(view)


	# add indent if previous line matches this
	extra_indents_before = {
		'':
		[
			r'[{<(\[]$',
		],
		r'python':
		[
			r'^\s*if\s.*:$',
			r'^\s*elif\s.*:$',
			r'^\s*else\s*:$',
			r'^\s*for\s.*:$',
			r'^\s*while\s.*:$',
			r'^\s*def\s.*:$',
			r'^\s*class\s.*:$',
		],
		r'lua':
		[
			r'^\s*if\s.*then$',
			r'^\s*else\s*$',
			r'^\s*for\s',
			r'^\s*while\s',
			r'^\s*function\s',
		],
		r'matlab':
		[
			r'^\s*for\s.*(?<!end)$',
			r'^\s*parfor\s.*(?<!end)$',
			r'^\s*if\s.*(?<!end)$',
			r'^\s*else($|\s.*(?<!end))$',
			r'^\s*elseif\s.*(?<!end)$',
			r'^\s*while\s.*(?<!end)$',
			r'^\s*function\s',
			r'^\s*classdef\s',
			r'^\s*properties(\W|$)',
			r'^\s*methods(\W|$)',
			r'^\s*case\s',
		],
		r'java|cs|c\+\+|js':
		[
			r'^\s*for[\s(].*(?<!(;|}))$',
			r'^\s*if[\s(].*(?<!(;|}))$',
			r'^\s*else[\s(].*(?<!(;|}))$',
			r'^\s*elseif[\s(].*(?<!(;|}))$',
			r'^\s*while[\s(].*(?<!(;|}))$',
		]
	}

	connect_below = r'^\s*(else|elseif|end|}|]|\))'

	# add indent if next line matches this
	extra_indents_after = {
		'':
		[
			r'^\s*[}>)\]]',
		],
		r'python':
		[
			r'^\s*else\s*:$',
			r'^\s*elif\s.*:$',
		],
	}

	# reduce indent if previous line matches this
	less_indents_before = {
		'python':
		[
			r'^\s*return$',
			r'^\s*continue$',
			r'^\s*break$',
		]
	}

	# reduce indent if paste_content starts with this
	less_indents_for = {
		'matlab':
		[
			r'^\s*case'
		],
		r'cs|c\+\+':
		[
			r'^\s*public:',
			r'^\s*private:',
			r'^\s*protected:',
		]
	}

	# Force indent if paste content starts with this
	force_indent = {
		'python':
		{
			r'^\s*def\s': 'smallest',
			r'^\s*class\s': 0,
		}
	}

	def normalise_line_endings(self, string):
		# Reset line ending characters
		string = re.sub(r'\r\n?', '\n', string)
		# Strip trailing whitespace
		string = re.sub(r'[ \t]*\n', '\n', string)

		return string

	def apply_line_endings(self, string):
		line_endings = self.view.settings().get('default_line_ending')

		if line_endings == 'windows':
			string = string.replace('\n', '\r\n')
		elif line_endings == 'mac':
			string = string.replace('\n', '\r')

		return string


	def indent_text(self, text, indent):
		use_spaces = self.view.settings().get('translate_tabs_to_spaces')
		tab_size = int(self.view.settings().get('tab_size', 4))
		(_, min_length) = min_indentation_of_lines(self.view, text, tab_size)
		in_len = length_of_indentation(indent, tab_size)
		lines = text.split('\n')
		new_lines = []
		for line in lines:
			# print("line: --%s== %d" % (line, len(line)))
			if len(line) == 0:
				new_lines.append(str(''))
				continue
			(line_indent, line_ind_len, line_rest) = indentation_of_line(line, tab_size)
			line_indent = re.sub(r'\t', ' ' * tab_size, line_indent)
			# print("line_indent: --%s--" % re.sub(r'\t', r'T', line_indent))
			line_indent = line_indent[min_length:]
			if not use_spaces:
				line_indent = re.sub(' ' * tab_size, '\t', line_indent)
			new_line = indent + line_indent + line_rest
			if len(line_rest) == 0:
				new_line = '';
			new_lines.append(str(new_line))

		return '\n'.join(new_lines)




	def find_indentation_before(self, point):
		return find_indention_at(self.view, find_code_before(self.view, point))

	def find_indentation_after(self, point):
		return find_indention_at(self.view, find_code_after(self.view, point))


	def find_indent_near(self, point, include_current_line, paste_content):
		tab_size = int(self.view.settings().get('tab_size', 4))

		tabs = [tabs for syntax, fis in iter(self.force_indent.items()) if re.match(syntax, self.current_syntax) is not None for fi, tabs in iter(fis.items()) if re.match(fi, paste_content)]
		if tabs: tabs = tabs[0]
		if isinstance(tabs, int):
			return ('\t' * tabs, tabs * tab_size, '')

		if self.current_syntax == 'python':
			if tabs == 'smallest':
				(indent, in_len, rest) = self.find_biggest_indent_near(point, include_current_line, smallest=True)
			else:
				(indent, in_len, rest) = self.find_indent_nearest(point, include_current_line)
		else:
			(indent, in_len, rest) = self.find_biggest_indent_near(point, include_current_line)

		less_indent = any(re.match(fi, paste_content) for syntax, fis in iter(self.less_indents_for.items()) if re.match(syntax, self.current_syntax) is not None for fi in fis)
		if less_indent:
			return ('\t' * int((in_len - tab_size) / tab_size), in_len - tab_size, rest)

		return (indent, in_len, rest)


	def find_indent_nearest(self, point, include_current_line=False):
		tab_size = int(self.view.settings().get('tab_size', 4))
		(row,_) = self.view.rowcol(point)
		point = self.view.text_point(row, 0)

		pb = find_code_before(self.view, point)
		(rowb,_) = self.view.rowcol(pb)
		(indb, lenb, rest_before) = find_indention_at(self.view, pb)

		pa = find_code_after(self.view, point)
		(rowa,_) = self.view.rowcol(pa)
		(inda, lena, rest_after) = find_indention_at(self.view, pa)

		matchb = self.matches_extra_indent(self.extra_indents_before, rest_before)
		matcha = self.matches_extra_indent(self.extra_indents_after, rest_after)
		
		# print("rest_before:--%s--" % rest_before)
		# print("rest_after:--%s--" % rest_after)
		# print("matchb: %d matcha: %d" % (matchb, matcha))
		
		if matcha and (not matchb or lena > lenb): return (inda + '\t', lena + tab_size, rest_after)
		if matchb: return (indb + '\t', lenb + tab_size, rest_before)

		matchc = self.matches_extra_indent(self.less_indents_before, rest_before)
		if matchc: return ('\t' * int((lenb - tab_size) / tab_size), lenb - tab_size, rest_before)

		if pa == -1 or abs(row - rowb) <= abs(row - rowa):
			return (indb, lenb, rest_before)
		else:
			return (inda, lena, rest_after)




	def matches_extra_indent(self, extra_indents, text):
		return any(re.match(ei, text) for syntax, eis in iter(extra_indents.items()) if re.match(syntax, self.current_syntax) is not None for ei in eis)


	def find_biggest_indent_near(self, point, include_current_line=False, smallest=False):
		tab_size = int(self.view.settings().get('tab_size', 4))
		(row,col) = self.view.rowcol(point)
		point_above = self.view.text_point(row, 0)
		(indent_before, lenb, rest_before) = self.find_indentation_before(point_above)
		(indent_after, lena, rest_after) = self.find_indentation_after(point_above)

		forced_a = False
		forced_b = False
		if self.matches_extra_indent(self.extra_indents_before, rest_before):
			(indent_before, lenb, rest_before) = (indent_before +  '\t', lenb +  tab_size, rest_before)
			forced_b = True
			# print("Forced before due to %s" % rest_before)
		if self.matches_extra_indent(self.extra_indents_after, rest_after):
			(indent_after, lena, rest_after) = (indent_after +  '\t', lena +  tab_size, rest_after)
			forced_a = True
			# print("Forced after due to %s" % rest_after)

		if self.matches_extra_indent(self.less_indents_before, rest_before):
			(indent_after, lena, rest_after) = ('\t' * int((lenb - tab_size) / tab_size), lenb - tab_size, rest_before)
			# print("Extra indents less due to %s" % rest_before)

		if smallest:
			if lena <= lenb: return (indent_after, lena, rest_after)
			else: return (indent_before, lenb, rest_before)

		if lena > lenb and (forced_a or not forced_b) or (forced_a and not forced_b):
			(indent, in_len, rest) = (indent_after, lena, rest_after)
		else:
			(indent, in_len, rest) = (indent_before, lenb, rest_before)

		return (indent, in_len, rest)

	def is_single_line(self, text):
		return '\n' not in text[:-1] and text[-1] == '\n'


	def add_space_around(self, text, region):
		"""Prepares a piece of text for insertion at given region. Helper for other addons at this time."""

		text_before = get_text_after(self.view, region.begin(), False)
		text_after = get_text_after(self.view, region.end(), True)
		char_before, space_before = split_text_before(text_before)
		char_after, space_after = split_text_after(text_after)

		# print("text_before:--%s--  text_after:--%s--" % (text_before, text_after))
		# print("space_before:--%s-- char_before:--%s--" % (space_before, char_before))
		# print("space_after:--%s-- char_after:--%s--" % (space_after, char_after))

		text = text.strip()
		char_before_text, space_before_text = split_text_before(text[:-1])
		char_after_text, space_after_text = split_text_after(text[1:])

		keyForLookup = ci.GetKeyForLookup(text[0])
		keyData = ci.GetDataForKey(self.view, region.begin(), keyForLookup, self.current_syntax)
		if ci.supported(self.view, region.begin(), keyData) and \
			not space_before and ci.ShouldHaveSpaceBefore(keyData, char_before, char_after_text, region.begin()):
			text = ' ' + text

		keyForLookup = ci.GetKeyForLookup(text[-1])
		keyData = ci.GetDataForKey(self.view, region.end(), keyForLookup, self.current_syntax)
		if ci.supported(self.view, region.end(), keyData) and \
			not space_after and ci.ShouldHaveSpaceAfter(keyData, char_before_text, char_after):
			text = text + ' '

		return text


	def insertTextAtRegion(self, edit, region, text, selectResult):
		is_single_line = self.is_single_line(text)
		if selectResult or is_single_line:
			self.view.sel().clear()
			# This doesn't work, because region indicates where to insert the text, not where our current selection is
			# self.view.sel().subtract(region)

		if not region.empty():
			self.view.erase(edit, region)
			region.a = region.b = region.begin()

		# Use correct spacing around paste content
		if '\n' not in text:
			text = self.add_space_around(text, region)
			
		count = self.view.insert(edit, region.begin(), text)

		if selectResult:
			self.view.sel().add(sublime.Region(region.begin(), region.begin() + count))
		elif is_single_line:
			self.view.sel().add(region.begin())



	def run(self, edit):
		self.perform_clever_paste(edit, sublime.get_clipboard())


	def perform_clever_paste(self, edit, paste_content):
		paste_content = self.normalise_line_endings(paste_content)
		pc_is_multiline = '\n' in paste_content[:-1]
		pc_has_newlines = '\n' in paste_content
		view = self.view;

		if pc_has_newlines:
			paste_content = paste_content.rstrip() + "\n"

		self.current_syntax = get_current_syntax(view)
		selectResult = self.current_syntax == "python" and pc_is_multiline
		tab_size = int(view.settings().get('tab_size', 4))

		# Make a copy of the regions in the current selection
		regions = []
		sel = view.sel()
		for region in sel:
			regions.append(region)

		# Insert new text from back to front, so the earlier regions are still correct
		regions.sort(key = lambda region: region.begin(), reverse = True)


		for region in regions:
			text = view.substr(region)
			is_sel_multiline = '\n' in text
			is_sel_empty = region.empty()
			# is_sel_whitespace = is_whitespace(text)
			is_sel_at_start = view.classify(region.begin()) & sublime.CLASS_LINE_START


			if is_sel_multiline:
				region = expand_selection_to_lines(view, region)
				text = view.substr(region)
				if is_whitespace(text):
					(indent, in_len, _) = self.find_indent_near(int((region.begin() + region.end()) / 2), False, paste_content)
				else:
					(indent, in_len) = min_indentation_of_lines(view, text, tab_size)
				paste_content = self.indent_text(paste_content, indent)
				if not pc_has_newlines:
					paste_content = paste_content + '\n'
				self.insertTextAtRegion(edit, region, paste_content, selectResult)
			else:
				if pc_has_newlines:
					if not is_sel_empty: # small selection, on same line
						(indent, in_len, _) = self.find_indent_near(region.begin(), False, paste_content)
						paste_content = self.indent_text(paste_content, indent)
						region = view.full_line(region)

						self.insertTextAtRegion(edit, region, paste_content, selectResult)
					else: # just a cursor
						line = view.substr(view.line(region.begin()))
						if is_whitespace(line): # cursor on empty line
							# if is_sel_at_start:
							(indent, in_len, _) = self.find_indent_near(region.begin(), True, paste_content)
							paste_content = self.indent_text(paste_content, indent)
							if paste_content.endswith('\n') and re.match(self.connect_below, view.substr(view.line(line_below(view, region.end())))):
								paste_content = paste_content[:-1]
							region = view.line(region)
							self.insertTextAtRegion(edit, region, paste_content, selectResult)
						else: # cursor on non-empty line
							(indent, in_len, _) = self.find_indent_near(region.begin(), False, paste_content)
							paste_content = self.indent_text(paste_content, indent)
							(row,col) = view.rowcol(region.begin())
							point = view.text_point(row, 0)
							paste_content = self.indent_text(paste_content, indent)
							self.insertTextAtRegion(edit, sublime.Region(point, point), paste_content, selectResult)
							# view.insert(edit, point, paste_content)
				else: # paste_content is plain string (no newlines)
					if not is_sel_empty: # small selection, on same line
						selectResult = False
						self.insertTextAtRegion(edit, region, paste_content, selectResult)
					else: # just a cursor
						line = view.substr(view.line(region.begin()))
						if is_whitespace(line): # cursor on empty line
							(indent, in_len, _) = self.find_indent_near(region.begin(), True, paste_content)
							if is_sel_at_start and in_len > 0:
								paste_content = self.indent_text(paste_content, indent)
								region = view.line(region)
								if not re.match(self.connect_below, view.substr(view.line(region.end() + 1))):
									paste_content += '\n'
							self.insertTextAtRegion(edit, region, paste_content, selectResult)

						# line is a single } or ] or end
						elif re.match(self.connect_below, line):
							line_start = line_begin(view, region.begin())
							(indent, in_len, _) = self.find_indent_near(line_start, True, paste_content)
							paste_content = self.indent_text(paste_content, indent)
							paste_content += '\n'
							self.insertTextAtRegion(edit, sublime.Region(line_start, line_start), paste_content, selectResult)
						else:
							self.insertTextAtRegion(edit, region, paste_content, False)


