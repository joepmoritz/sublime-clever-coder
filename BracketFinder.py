import sublime
import sys


def match(view, pos, forward, what = "both"):
	bf = BracketFinder(view, 1)
	return bf.match(pos, forward, what)


class BracketFinder():

	def __init__(self, view, num_sel):
		self.view = view
		self.bhmod = sys.modules["BracketHighlighter"]

		self.bhc = self.bhmod.bh_core.BhCore(
			True,
			False,
			False,
			True,
			False,
			None,
			None,
			True
		)

		self.bhc.view = view
		self.bhc.sub_search_mode = False
		self.bhc.recursive_guard = False
		self.bhc.init_match(num_sel)


	def match(self, pos, forward, what = "both"):
		delta = 1 if forward else -1
		region = sublime.Region(pos + delta, pos + delta)
		self.bhc.bracket_style = None
		self.bhc.search = self.bhmod.bh_search.Search(
			self.view, self.bhc.rules,
			region, self.bhc.selection_threshold if not self.bhc.ignore_threshold else None
		)

		if what == "quotes" or what == "both":
			# last param for match_scope_brackets indicates if scope search is adjacent
			# LEFT for searches to the left, so direction == back
			d = self.bhmod.bh_search.BH_ADJACENT_RIGHT if forward else self.bhmod.bh_search.BH_ADJACENT_LEFT
			left, right, bracket, sub_matched = self.bhc.match_scope_brackets(region, d)

		if what == "brackets" or what == "both" and not left and not right:
			left, right, adj_scope = self.bhc.match_brackets(region, scope=None)

		# print(left)
		# print(right)
		# print(pos)

		if forward and left and left.begin == pos and right:
			return right.end
		if not forward and right and right.end == pos and left:
			return left.begin

		return pos


	def match_bracket(self, pos, forward):
		return self.match(pos, forward, "brackets")


	def match_quote(self, pos, forward):
		return self.match(pos, forward, "quotes")






