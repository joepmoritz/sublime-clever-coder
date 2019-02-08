import sublime, sublime_plugin
from . import CleverDelete
from .utils import *




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







class CleverCutCommand(sublime_plugin.TextCommand):

	def run(self, edit):
		self.view.run_command('cut')

		regions = list(self.view.sel())

		for region in reversed(regions):
			begin, end = region.begin(), region.end()

			begin, end = CleverDelete.cleanup(self.view, begin, end, True)
			region = sublime.Region(begin, end)
			self.view.erase(edit, region)


