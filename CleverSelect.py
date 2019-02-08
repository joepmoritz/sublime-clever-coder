import sublime, sublime_plugin
from .utils import *


# CleverSelectParagraphStarts =
# [
# 	r'^\s*if.*:',
# ]

CleverSelectParagraphEnd = [
	r'^[\s})\],;]+$'
]

class CleverSelectCommand(sublime_plugin.TextCommand):

	def selectLine(self, region, direction):
		if region.empty():
			self.view.sel().subtract(region)
			region = self.view.full_line(region)

			# For when cursor is on empty line at end of file: full_line won't do anything
			text = self.view.substr(region)
			if '\n' not in text:
				rbegin = self.view.find_by_class(region.begin(), False, sublime.CLASS_LINE_START)
				region = sublime.Region(rbegin, region.end())

			newRegion = region
			if direction == "up":
				newRegion = sublime.Region(region.end(), region.begin())
			self.view.sel().add(newRegion)
		else:
			if not self.view.classify(region.begin()) & sublime.CLASS_LINE_START or not self.view.classify(region.end()) & sublime.CLASS_LINE_START:
				if direction == "down":
					(row, col) = self.view.rowcol(region.end())
					self.view.sel().add(sublime.Region(region.begin(), self.view.text_point(row + 1, col)))
				else:
					(row, col) = self.view.rowcol(region.begin())
					self.view.sel().add(sublime.Region(region.end(), self.view.text_point(row - 1, col)))
			else:
				if direction == "down":
					line_begin = self.view.find_by_class(region.end(), True, sublime.CLASS_LINE_START)
					self.view.sel().add(sublime.Region(region.begin(), line_begin))
				else:
					line_begin = self.view.find_by_class(region.begin(), False, sublime.CLASS_LINE_START)
					self.view.sel().add(sublime.Region(region.end(), line_begin))
 

	def selectParagraph(self, region, direction):

		forward = direction == "down"

		if region.empty():
			(_, current_indent, _) = find_indention_at(self.view, region.begin())
			if is_line_empty(self.view, region.begin()):
				current_indent = -1
		else:
			tab_size = int(self.view.settings().get('tab_size', 4))
			text = self.view.substr(region)
			(_, current_indent) = min_indentation_of_lines(self.view, text, tab_size)
			if is_whitespace(text): current_indent = -1


		# print("indent: %d" % current_indent)

		# pb = self.findParagraphEnd(region.begin(), direction == "down", current_indent)
		# # pb = self.findParagraphStart(pb, direction == "down", current_indent)
		# self.view.sel().subtract(region)
		# self.view.sel().add(sublime.Region(pb, pb))

		# return

		if region.empty():
			position = region.begin()
			if is_line_empty(self.view, position):
				if forward:
					start = self.findParagraphStart(position, True, -1, True)
				else:
					start = self.findParagraphStart(position, False, -1, True)
				(_, start_indent, _) = find_indention_at(self.view, start)
				end = self.findParagraphEnd(start, True, start_indent)
			else:
				start = self.findParagraphStart(position + 1, False, current_indent, True)
				end = self.findParagraphEnd(position - 1, True, current_indent)

			end = end + 1
			if not forward: (start, end) = (end, start)
			self.view.sel().subtract(region)
			region = sublime.Region(start, end)
			self.view.sel().add(region)
			self.view.show(region)
		else:
			if forward:
				end = self.findParagraphEnd(region.end(), True, current_indent)
				self.view.sel().add(sublime.Region(region.begin(), end))
				self.view.show(end)
			else:
				start = self.findParagraphStart(region.begin(), False, current_indent, False)
				self.view.sel().add(sublime.Region(region.end(), start))
				self.view.show(start)



	# Not very good this one, broken for up search! only use down for now
	def findParagraphEnd(self, fromPosition, forward, indentation):
		nextStart = self.findParagraphStart(fromPosition, forward, indentation, False)
		codeBefore = find_code_before(self.view, nextStart)

		if codeBefore == -1:
			return nextStart

		if (codeBefore <= fromPosition) == forward:
			(_, current_indent, _) = find_indention_at(self.view, nextStart)
			nextStart = self.findParagraphStart(nextStart + 1, forward, current_indent, False)
			codeBefore = find_code_before(self.view, nextStart)

		return codeBefore



	def findParagraphStart(self, fromPosition, forward, indentation, ignoreComments):
		position = fromPosition

		iterationCount = 0
		maxIteration = 10000

		while iterationCount < maxIteration:
			iterationCount += 1

			nextPosition = self.view.find_by_class(position, forward, sublime.CLASS_LINE_START)
			if nextPosition == position:
				return position
			position = nextPosition

			lineIsEmpty = is_line_empty(self.view, position)
			isComment = is_line_comment(self.view, position)
			(_, current_indent, _) = find_indention_at(self.view, position)

			if not lineIsEmpty and indentation < 0:
				indentation = current_indent

			posAbove = line_above(self.view, position)
			lineAboveIsEmpty = is_line_empty(self.view, posAbove)
			lineAboveIsComment = is_line_comment(self.view, posAbove)
			(_, indentAbove, _) = find_indention_at(self.view, posAbove)
			text_above = self.view.substr(self.view.line(posAbove))

			if not lineIsEmpty and (
				(current_indent <= indentation and lineAboveIsEmpty) or
				(not lineAboveIsEmpty and current_indent < indentation and current_indent != indentAbove) or
				(not lineAboveIsEmpty and indentAbove < indentation and current_indent != indentAbove) or
				(isComment and not lineAboveIsEmpty and not lineAboveIsComment and current_indent <= indentation and not ignoreComments) or
				(not lineAboveIsEmpty and indentAbove <= indentation and any(re.match(r, text_above) for r in CleverSelectParagraphEnd))
				):
				return position

			if not lineIsEmpty and current_indent < indentation:
				indentation = current_indent






	def run(self, edit, type, direction):

		regions = list(self.view.sel())

		if type == "line":
			for region in reversed(regions):
				self.selectLine(region, direction)
		elif type == "paragraph":
			for region in reversed(regions):
				self.selectParagraph(region, direction)
		elif type == "piece":
			forward = direction == "forward"
			self.view.sel().clear()
			for region in reversed(regions):
				begin, end = region.begin(), region.end()

				if forward:
					end = find_piece_end(self.view, begin, end, forward)
					# end = clean_up_right(self.view, begin, end)
					region = sublime.Region(begin, end)
				else:
					begin = find_piece_end(self.view, begin, end, forward)
					# begin = clean_up_left(self.view, begin, end)
					region = sublime.Region(end, begin)


				self.view.sel().add(region)






class CleverSelectListener(sublime_plugin.EventListener):

	def on_query_context(self, view, key, operator, operand, match_all):
		if key == "CleverSelect":
			if operand == "line":
				for region in view.sel():
					if not region.empty():
						if not view.classify(region.begin()) & sublime.CLASS_LINE_START or not view.classify(region.end()) & sublime.CLASS_LINE_START:
							return False
			return True
		else:
			return None
