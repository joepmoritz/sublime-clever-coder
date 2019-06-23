import sublime
import re
from . import BracketFinder

def find_code_before(view, point):
	classes = sublime.CLASS_WORD_END | sublime.CLASS_PUNCTUATION_END
	p = view.find_by_class(point, False, classes)
	if view.classify(p) & sublime.CLASS_LINE_START:
		return -1
	return p

def find_code_after(view, point):
	classes = sublime.CLASS_WORD_START | sublime.CLASS_PUNCTUATION_START
	p = view.find_by_class(point, True, classes)
	if view.classify(p) & sublime.CLASS_LINE_END:
		return -1
	return p


def expand_selection_to_lines(view, region):
	# changes selection to start at begining of first line
	# and end at the end of last line
	# includes newline at end
	# Will remove extra whitespace before/after
	# Keeps cursor at same end

	if region.empty():
		return view.full_line(region)

	t = view.substr(region)
	is_sel_whitespace = is_whitespace(t)

	(rbegin, rend) = (region.begin(), region.end())

	# part of line selected at the beginning, user might want this line

	if is_sel_whitespace:
		if not view.classify(rbegin) & sublime.CLASS_LINE_START:
			rbegin = view.find_by_class(rbegin, False, sublime.CLASS_LINE_START)
	else:
		rbegin = view.find_by_class(rbegin, False, sublime.CLASS_LINE_END)
		rbegin = view.find_by_class(rbegin, True, sublime.CLASS_WORD_START | sublime.CLASS_PUNCTUATION_START)
		if not view.classify(rbegin) & sublime.CLASS_LINE_START:
			rbegin = view.find_by_class(rbegin, False, sublime.CLASS_LINE_START)


	# part of line selected at the end, user might want this line
	if not view.classify(rend) & sublime.CLASS_LINE_START:
		rend = view.find_by_class(rend, True, sublime.CLASS_LINE_START)

	if not is_sel_whitespace:
		rend = view.find_by_class(rend, False, sublime.CLASS_WORD_END | sublime.CLASS_PUNCTUATION_END)
		rend = view.find_by_class(rend, True, sublime.CLASS_LINE_START)


	if region.a > region.b:
		return sublime.Region(rend, rbegin)
	else:
		return sublime.Region(rbegin, rend)




def is_whitespace(text):
	return re.match(r'^\s*$', text) is not None

def is_whitespace_singleline(text):
	return re.match(r'^\s*$', text) is not None

def is_line_empty(view, point):
	return is_whitespace(view.substr(view.full_line(point)))

def get_current_syntax(view, point = 0):
	scope_name = view.scope_name(point)
	# print("scope_name:--%s--" % (scope_name))

	if 'php' in scope_name:
		return 'php'

	m = re.match(r'\w+\.([^ \t]+)', scope_name)
	return m.group(1)


def length_of_indentation(text, tab_size):
	# Returns lengths of indentation. Assumes text is only whitespace!!
	return text.count('\t') * tab_size + text.count(' ')


def indentation_of_line(text, tab_size):
	m = re.match(r'^([ \t]*)(.*)$', text)
	if m:
		return (m.group(1), length_of_indentation(m.group(1), tab_size), m.group(2))
	else:
		return None

def find_indention_at(view, point_or_region):
	tab_size = int(view.settings().get('tab_size', 4))
	r = view.line(point_or_region)
	t = view.substr(r)
	return indentation_of_line(t, tab_size)

def min_indentation_of_lines(view, text, tab_size):
	ignore_empty_line = re.match(r'^\s*$', text) is not None

	min_length = 1000
	min_indent = ''
	lines = filter(None, text.split('\n'))
	for line in lines:
		if not ignore_empty_line or not re.match(r'^\s*$', line):
			(indent, in_len, _) = indentation_of_line(line, tab_size)
			if in_len < min_length:
				min_length = in_len
				min_indent = indent

	return (min_indent, min_length)


def line_above(view, point):
	(row, col) = view.rowcol(point)
	return view.text_point(row - 1, 0)

def line_below(view, point):
	(row, col) = view.rowcol(point)
	return view.text_point(row + 1, 0)

def line_begin(view, point):
	(row, col) = view.rowcol(point)
	return view.text_point(row, 0)

def line_end(view, point, forward = True):
	c = sublime.CLASS_LINE_END if forward else sublime.CLASS_LINE_START
	if view.classify(point) & c:
		return point
	else:
		return view.find_by_class(point, forward, c)

def move_pos(view, pos, amount, forward):
	if forward: return min(view.size(), pos + amount)
	return max(0, pos - amount)


def get_text_after(view, pos, forward):
	return view.substr(sublime.Region(pos, move_pos(view, pos, 200, forward)))

def split_text_before(text_before):
	m = re.search(r'(.*?)(\s*)$', text_before)
	char_before = m.group(1)
	space_before = m.group(2)
	return (char_before, space_before)


def split_text_after(text_after):
	m = re.search(r'^(\s*)(.*)', text_after)
	space_after = m.group(1)
	char_after = m.group(2)
	return (char_after, space_after)

def get_character_after(view, pos, forward):
	return view.substr(pos if forward else pos - 1)

def is_line_comment(view, point):
	line_start = line_begin(view, point)
	(row, col) = view.rowcol(line_start)

	next_char = view.find('\S', line_start)
	(row_next, column_next) = view.rowcol(next_char.begin())

	if row != row_next: return False
	return (view.match_selector(next_char.begin(), 'comment.line') or
		view.match_selector(next_char.begin(), 'comment.block'))


def skip_over(view, pattern, pos, forward):
	text_after = get_text_after(view, pos, forward)
	if not forward: text_after = text_after[::-1]

	m = re.match(pattern, text_after)
	if not m: return pos
	if forward: return pos + m.end(0)
	return pos - m.end(0)


def find_operator_end(view, pos, forward):
	return skip_over(view, r'[=+\-*/^&|%@!~?<>]*', pos, forward)


def find_name_end(view, pos, forward):
	return skip_over(view, r'[A-Za-z0-9_]*(\*|&&|&)?', pos, forward)


def find_number_end(view, pos, forward):
	return skip_over(view, r'[0-9-.][A-Za-z0-9_.]*', pos, forward)


def find_piece_end(view, begin, end, forward):
	front, back = (begin, end) if forward else (end, begin)

	if forward: skip_pattern = r'([ \t,.)}\]>]|->|::|\s)*'
	else: skip_pattern = r'([ \t,.({\[<]|->|::|\s)*'
	back = skip_over(view, skip_pattern, back, forward)

	char = get_character_after(view, back, forward)
	text_after = get_text_after(view, back, forward)

	# print("text_after: %s" % text_after)

	if forward and char in ['(', '[', '{', '<']:
		new_back = BracketFinder.match(view, back, forward, "brackets")
	elif not forward and char in [')', ']', '}', '>']:
		new_back = BracketFinder.match(view, back, forward, "brackets")
	elif char in ['"', '\'']:
		new_back = BracketFinder.match(view, back, forward, "quotes")
	elif view.score_selector(back if forward else back - 1, 'constant.numeric'):
		new_back = find_number_end(view, back, forward)
	elif is_name_text(text_after, forward):
		new_back = find_name_end(view, back, forward)
	elif is_operator_char(char):
		new_back = find_operator_end(view, back, forward)
	else:
		new_back = back

	if new_back == back: new_back += 1 if forward else -1

	return new_back


def is_name_text(text, forward):
	pattern = r'^\w' if forward else r'(\w|\w(\*|&&|&))$'
	return re.search(pattern, text)


def is_name_char(char):
	oc = ord(char)
	ranges = [['a', 'z'], ['A', 'Z'], ['0', '9'], ['_', '_']]
	return any(oc >= ord(r[0]) and oc <= ord(r[1]) for r in ranges)

def is_number_char(char):
	oc = ord(char)
	ranges = [['a', 'z'], ['A', 'Z'], ['0', '9'], ['_', '_'], ['.', '.'], ['-', '-']]
	return any(oc >= ord(r[0]) and oc <= ord(r[1]) for r in ranges)

operator_characters = ['=', '+', '-', '*', '/', '^', '&', '|', '%', '@', '!', '~', '?', '<', '>']

def is_operator_char(char):
	return char in operator_characters
