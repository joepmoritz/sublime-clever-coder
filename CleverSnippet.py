import sublime, sublime_plugin
import os
from .CleverPaste import CleverPasteCommand
from .utils import *


class CleverSnippetCommand(sublime_plugin.TextCommand):
	snippets = {
		'brace': [
			{
				'before': '${1:statement}',
				'after': '',
				'syntax': 'python'
			},
			{
				'before': '${1:statement}',
				'after': 'end\n',
				'syntax': 'matlab'
			},
			{
				'before': '{',
				'after': '}\n',
				'syntax': ''
			}
		],
		'if': [
			{
				'before': 'if $1:',
				'after': '',
				'syntax': 'python'
			},
			{
				'before': 'if $1',
				'after': 'end\n',
				'syntax': 'matlab'
			},
			{
				'before': 'if ($1) {',
				'after': '}\n',
				'syntax': 'js'
			},
			{
				'before': 'if ($1)\n{',
				'after': '}\n',
				'syntax': ''
			}
		],
		'if_single_line': [
			{
				'before': 'if $1:',
				'after': '',
				'syntax': 'python'
			},
			{
				'before': 'if $1 ,end',
				'after': '',
				'syntax': 'matlab'
			},
			{
				'before': 'if ($1) $2',
				'after': '',
				'syntax': ''
			}
		],
		'elseif': [
			{
				'before': 'elif $1:',
				'after': '',
				'syntax': 'python',
				'reduceIndent': True,
			},
			{
				'before': 'elsif $1 ,end',
				'after': '',
				'syntax': 'matlab'
			},
			{
				'before': 'else if ($1) {',
				'after': '}\n',
				'syntax': 'js'
			},
			{
				'before': 'elseif ($1) $2',
				'after': '',
				'syntax': ''
			}
		],
		'else': [
			{
				'before': 'else:',
				'after': '',
				'syntax': 'python',
				'reduceIndent': True,
			},
			{
				'before': 'else',
				'after': '',
				'syntax': 'matlab',
				'reduceIndent': True,
			},
			{
				'before': 'else {',
				'after': '}\n',
				'syntax': 'js',
			},
			{
				'before': 'else\n{',
				'after': '}\n',
				'syntax': '',
			}
		],
		'for': [
			{
				'before': 'for ${1:item} in ${2:list}:',
				'after': '',
				'syntax': 'python'
			},
			{
				'before': 'for ${1:item} = ${2:list}',
				'after': 'end\n',
				'syntax': 'matlab'
			},
			{
				'before': 'for (${1:initial})\n{',
				'after': '}\n',
				'syntax': ''
			}
		],
		'def': [
			{
				'before': 'def ${1:name}(${2:args}):',
				'after': '',
				'syntax': 'python'
			},
			{
				'before': 'function ${1:#FILENAME#}(${2:args})',
				'after': 'end\n',
				'syntax': 'matlab'
			},
			{
				'before': 'function ${1:func}(${2:args}) {',
				'after': '}\n',
				'syntax': 'js'
			},
			{
				'before': '${1:func}(${2:args}) {',
				'after': '}\n',
				'syntax': 'java'
			},
			{
				'before': '${1:func}(${2:args})\n{',
				'after': '}\n',
				'syntax': ''
			},
		],
		'while': [
			{
				'before': 'while ${1:condition}:',
				'after': '',
				'syntax': 'python'
			},
			{
				'before': 'while ${1:condition}',
				'after': 'end\n',
				'syntax': 'matlab'
			},
			{
				'before': 'while (${1:condition})\n{',
				'after': '}\n',
				'syntax': ''
			}
		],

		'class': [
			{
				'before': 'class ${1:name}(${2:object}):',
				'after': '',
				'syntax': 'python'
			},
			{
				'before': 'classdef ${1:name}\n\tproperties\n\n\tend\n\n\tmethods\n\n\tend\n',
				'after': 'end',
				'syntax': 'matlab'
			},
			{
				'before': 'class ${1:name}\n{',
				'after': '};\n',
				'syntax': ''
			}
		],

		'try': [
			{
				'before': 'try:',
				'after': 'except Exception as e:\n\traise e\n',
				'syntax': 'python'
			},
			{
				'before': 'try',
				'after': 'catch\nend\n',
				'syntax': 'matlab'
			},
			{
				'before': 'try\n{',
				'after': '}\ncatch (Exception e)\n{\n}\n',
				'syntax': 'java'
			},
			{
				'before': 'try\n{',
				'after': '}\ncatch (const std::exception& e)\n{\n}\n',
				'syntax': ''
			}
		],
	
		'comment': [
			{
				'before': '/**\n * $0\n */',
				'after': '',
				'syntax': ''
			}
		],
	}

	def run(self, edit, type):


		view = self.view
		self.settings = view.settings()
		self.tab_size = int(self.settings.get('tab_size', 4))

		cpc = CleverPasteCommand(view)

		for region in view.sel():
			is_sel_empty = region.empty()
			scope_name = view.scope_name(region.begin())
			# print("Scope:%s"%scope_name)
			snippets = self.snippets[type]
			for snippet in snippets:
				if snippet['syntax'] in scope_name:
					break

			text_before = snippet['before']
			text_after = snippet['after']

			if view.file_name():
				text_before = text_before.replace('#FILENAME#', os.path.basename(view.file_name())[:-2]);
				text_after = text_after.replace('#FILENAME#', os.path.basename(view.file_name())[:-2]);


			################################################################
			# Set region to where we want the snippet
			view.sel().subtract(region)
			region = expand_selection_to_lines(view, region)
			text = view.substr(region)
			is_text_whitespace = is_whitespace(text)

			# if cursor on a code line, add new line after and set selection to that new line
			if is_sel_empty:
				view.insert(edit, region.begin(), "\n")
				region = sublime.Region(region.begin(), region.begin() + 1)
				text = "\n"
				is_text_whitespace = True
				is_sel_empty = True

			view.sel().add(region)
			################################################################



			################################################################
			# indent text
			if is_text_whitespace:
				(indent, in_len, _) = cpc.find_indent_near(region.begin(), True, text_before)
				# print("indent: %d" % length_of_indentation(indent, self.tab_size))
			else:
				(indent, in_len) = min_indentation_of_lines(view, text, self.tab_size)

			if 'reduceIndent' in snippet and snippet['reduceIndent']:
				indent = '\t' * int((in_len - self.tab_size) / self.tab_size)
				in_len = in_len - self.tab_size


			text_before = cpc.indent_text(text_before, indent)
			text_after = cpc.indent_text(text_after, indent)
			text = cpc.indent_text(text.rstrip(), '\t' + indent) + "\n"

			# if no code selected, amend snippet
			if not is_text_whitespace:
				text = "\n" + text
			# else:
			# 	text_before += "\n\t" + indent + "${5:stuff}"
			################################################################

			# print("text:--%s--" % text)
			# print("text_after: --%s--" % text_after)
			# print("text_before:--%s--"%text_before)
			# print("text_before: --%s--" % re.sub(r'\t', 'T', text_before))
			# print("text: --%s--" % re.sub(r'\n', 'N', text))

			# ################################################################
			# # Add new lines before & after
			# is_above_empty = is_line_empty(view, line_above(view, region.begin()))
			# (_, indent_above, _) = find_indention_at(view, line_above(view, region.begin()))
			# (_, indent_below, _) = find_indention_at(view, line_below(view, region.begin()))
			# if not is_above_empty and indent_above >= in_len:
			# 	text_before = "\n" + text_before
			# is_below_empty = is_line_empty(view, line_below(view, region.begin()))
			# if not is_below_empty and indent_below >= in_len:
			# 	text_after += "\n"
			# ################################################################



			################################################################
			# Insert snippet
			view.erase(edit, region)
			view.sel().subtract(region)
			view.insert(edit, region.begin(), text + text_after)
			view.sel().add(region.begin())
			view.run_command('insert_snippet', args={"contents": text_before});
			################################################################






