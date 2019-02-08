import sublime, sublime_plugin
from .utils import *
from .CleverDelete import clean_up_right, clean_up_left


def test():
	x = a + b * c-1
	x += a * b * [plop(c + d) + 1, c(), p]
	x = -5 - 4.0 + .9
	self.view.sel().clear((a * b), m)
	# a = self . view .9
	# c++
	# x = -5 - 4.0e5
	# int x = p->test();
	# int x = 5*p;


class CleverMoveCommand(sublime_plugin.TextCommand):

	def run(self, edit, type, direction):
		forward = direction == "forward"

		regions = list(self.view.sel())

		self.view.sel().clear()

		for region in reversed(regions):
			begin, end = region.begin(), region.end()

			if forward:
				end = max(find_piece_end(self.view, begin, end, forward), end + 1)
				# end = clean_up_right(self.view, begin, end)
				region = sublime.Region(end, end)
			else:
				begin = min(find_piece_end(self.view, begin, end, forward), begin - 1)
				# begin = clean_up_left(self.view, begin, end)
				region = sublime.Region(begin, begin)


			self.view.sel().add(region)
			self.view.show(region)


