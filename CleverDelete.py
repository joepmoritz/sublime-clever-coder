import sublime, sublime_plugin
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






def cleanup(view, begin, end, forward):
	if forward:
		end = clean_up_right(view, begin, end)
		begin = clean_up_left(view, begin, end)
	else:
		begin = clean_up_left(view, begin, end)
		end = clean_up_right(view, begin, end)

	return begin, end


def clean_up_right(view, begin, end):
	text_before = get_text_after(view, begin, False)
	text_after = get_text_after(view, end, True)

	# (.  where ( is any char that doesn't like a . and . is any connector
	# note: space is valid between . connector in Python, but who does that really?
	# So I ignore that situation here. That way, keywords followed by . work correctly.
	if not re.search(r'[\w)}\]]+$', text_before):
		end = skip_over(view, r'[ \t]*(\.|->)(?=[^0-9])', end, True)

	# (,  where ( is any char that doesn't like a ,
	if re.search(r'(^|[,({\[<:?=!])[ \t]*$', text_before):
		end = skip_over(view, r'[ \t]*,', end, True)

	# (\s where ( is any char that doesn't like whitespace to it's right
	if re.search(r'([ \t(\[{<])$', text_before):
		end = skip_over(view, r'[ \t]*', end, True)

	# (::  where ( is any char that doesn't like a :: and :: is any connector
	# This is mostly for C++, as you can't have ::
	if not re.search(r'[\w]+$', text_before):
		end = skip_over(view, r'[ \t]*(::)(?=[^0-9])', end, True)

	return end


def clean_up_left(view, begin, end):
	text_before = get_text_after(view, begin, False)
	text_after = get_text_after(view, end, True)

	# .)  where ) is any char that doesn't like a . and . is any connector
	if not re.search(r'^[\w]', text_after):
		begin = skip_over(view, r'(\.|::|->)[ \t]*', begin, False)

	# ,)  where ) is any char that doesn't like a ,
	if re.search(r'^[ \t\s]*[,)}\]>:?=]', text_after):
		begin = skip_over(view, r',[\s]*', begin, False)

	# \s) where ) is any char that doesn't like whitespace to it's left
	if not is_whitespace(text_before) and re.search(r'^(;?$|[\s)}\]>,])', text_after):
		begin = skip_over(view, r'[ \t]*', begin, False)

	return begin


class CleverDeleteCommand(sublime_plugin.TextCommand):

	def run(self, edit, type, direction):
		forward = direction == "forward"

		regions = list(self.view.sel())

		self.view.sel().clear()

		for region in reversed(regions):
			begin, end = region.begin(), region.end()

			if self.view.classify(begin) & sublime.CLASS_LINE_START:
				begin = skip_over(self.view, r'[ \t]*', begin, True)
				end = max(end, begin)

			if forward:
				end = max(find_piece_end(self.view, begin, i, forward) for i in range(begin, max(end, begin + 1)))
			else:
				begin = min(find_piece_end(self.view, i, end, forward) for i in range(min(begin, end - 1) + 1, end + 1))

			begin, end = cleanup(self.view, begin, end, forward)
			region = sublime.Region(begin, end)
			self.view.sel().add(region)


		self.view.run_command("add_to_kill_ring", {"forward": forward})

		if forward:
			self.view.run_command('right_delete')
		else:
			self.view.run_command('left_delete')


