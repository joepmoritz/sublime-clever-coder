import sublime, sublime_plugin
import re
from functools import partial
from .utils import *
from pprint import pprint as pp


# TODO: fix C++ templates <> by checking text before for the word template
# This means we need more text before available

CleverInsertIgnoreSyntaxes = [
    'plain',
    'dosbatch',
    'yaml',
    'shell.bash',
    'git.commit',
    'html.markdown',
    'git.ignore',
    'git-commit',
]
CleverInsertIgnoreScopes = ['comment']

JustInsertedSpace = False
LastInsertedData = ''
LastInsertedPoint = None
LatexIgnoreScopes = [
    'meta.group.braces.tex',
    'meta.group.brace.latex',
    'variable.parameter.function.latex',
    'constant.other.reference.citation.latex',
    'string.other.math',
    'variable.parameter.function.latex',
    'punctuation.definition.arguments.latex']

CleverInsertKeys = {
    ';': [
        {
            'syntax': ['matlab', 'java', 'c', 'cs', 'c++', 'js', 'java', 'html.basic', 'php'],
            'at_end': True,
            'no_space_keyword': True,
            # 'ignore_scope': ['string.quoted'],
        },
        {
            'syntax': ['tex.latex'],
            # 'space_left': r'.$',
            'space_right': r'[\w}\]]',
            'at_end': False,
        },
    ],
    "'": [
        {
            # No space around = in keyword args
            'syntax': 'python',
            'scope': ['meta.function-call', 'meta.function.parameters'],
            'snippet': "'${0:$SELECTION}'",
            'space_left': r'[;+*/%&|,:)\]}#<>\.]$',
            'space_right': r'^[+*/%&|(\[{#<>\.]',
        },
        {
            'syntax': 'python',
            'snippet': "'${0:$SELECTION}'",
            'space_left': r'[;=+*/%&|,:)\]}#<>\.]$', # f-strings
            'space_right': r'^[=+*/%&|(\[{#<>\.]',
        },
        {
            'snippet': "'${0:$SELECTION}'",
            'space_left': r'[;=+*/%&|,:)\]}#<>\.]$',
            'space_right': r'^[=+*/%&|(\[{#<>\w\.]',
        },
    ],
    '"': [
        {
            'syntax': 'python',
            'scope': ['meta.function-call', 'meta.function.parameters'],
            'snippet': '"${0:$SELECTION}"',
            'space_left': r'[;+*/%&|,:)\]}#<>\.]$', # f-strings
            'space_right': r'^[+*/%&|(\[{#<>\.]',
        },
        {
            'syntax': 'python',
            'snippet': '"${0:$SELECTION}"',
            'space_left': r'[;=+*/%&|,:)\]}#<>\.]$', # f-strings
            'space_right': r'^[=+*/%&|(\[{#<>\.]',
        },
        {
            'snippet': '"${0:$SELECTION}"',
            'space_left': r'[;=+*/%&|,:)\]}#<>\.]$',
            'space_right': r'^[=+*/%&|(\[{#<>\w\.]',
        },
    ],
    '(': [
        {
            'scope': ['string'],
            'snippet': '(${0:$SELECTION})',
        },
        {
            # No space around = inside function calls
            'snippet': '(${0:$SELECTION})',
            'syntax': 'python',
            'scope': ['meta.function-call', 'meta.function.parameters'],
            'space_left': r'[;+\-*/%&|,:#<]$',
            'space_right': r'^[+\-*/%&|#<>\w]',
        },
        {
            'snippet': '(${0:$SELECTION})',
            'space_left': r'[;=+\-*/%&|,:#<]$',
            'space_right': r'^[=+\-*/%&|#<>\w]',
        },
    ],
    '{': [
        {
            # No space around = inside function calls
            'syntax': 'python',
            'scope': ['meta.function-call', 'meta.function.parameters'],
            'snippet': '{${0:$SELECTION}}',
            'space_left': r'[;+\-*/%&|,:)\]}#<>]$',
            'space_right': r'^[+\-*/%&|#<>\w]',
        },
        {
            'syntax': ['c', 'c++'],
            'snippet': '{${0:$SELECTION}}',
            'space_left': r'[;=+\-*/%&|,:\]}#<]$',
            'space_right': r'^[=+\-*/%&|#<>\w]',
        },
        {
            'snippet': '{${0:$SELECTION}}',
            'space_left': r'[;=+\-*/%&|,:)\]}#<>]$',
            'space_right': r'^[=+\-*/%&|#<>\w]',
        },
    ],
    '[': [
        {
            # No space around = inside function calls
            'snippet': '[${0:$SELECTION}]',
            'syntax': 'python',
            'scope': ['meta.function-call', 'meta.function.parameters'],
            'space_left': r'[;+\-*/%&|,:#<>]$',
            'space_right': r'^[+\-*/%&|#<>\w]',
        },
        {
            'snippet': '[${0:$SELECTION}]',
            'space_left': r'[;=+\-*/%&|,:#<>]$',
            'space_right': r'^[=+\-*/%&|#<>\w]',
        },
    ],
    '<>': [
        {
            'snippet': '<${0:$SELECTION}>',
            'space_left': r'[;=+\-*/%&|,:#<>]$',
            'space_right': r'^[=+\-*/%&|#<>\w\.]',
        },
    ],
    '=': [
        {
            'syntax': ['xml', 'css', 'html.basic'],
            'space_left': r'[})\]]$',
            'space_right': r'^[{(\[]',
            'connect_right': r'^=',
            'connect_left': r'[-=+*/%&|~]$'
        },
        {
            'syntax': 'python',
            'scope': ['meta.function-call.arguments', 'meta.function.parameters'],
            'connect_right': r'^=',
            'connect_left': r'[-=+*/%&|~]$'
        },
        {
            'space_left': r'[\w\'"})\]]$',
            'space_right': r'^[\w\'"{(\[]',
            'connect_right': r'^=',
            'connect_left': r'[-=+*/%&|~]$'
        },
    ],
    '!':
    [
        {
            'syntax': ['tex.latex'],
            'space_right': r'^[\w]',
        },
        {
            'space_left': r'[=\w\'"})\]]$',
            'connect_right': r'^.',
        },
    ],
    '?':
    [
        {
            'syntax': ['tex.latex'],
            'space_right': r'^[\w]',
        },
        {
            'space_left': r'[=\w\'"})\]]$',
            'space_right': r'^[\w\'"{(\[]',
        },
    ],
    '~': [
        {
            'syntax': ['tex.latex'],
            'space_left': r'[+*/=&|\'"})\]]$',
        },
        {
            'space_left': r'[+*/=&|\w\'"})\]]$',
        }
    ],
    '+':
    [
        {
            'scope': ['meta.item-access'],
            'space_left': r'[\'"};]$',
            'space_right': r'^[\'"{]',
            'connect_right': r'^[=+]',
        },
        {
            'space_left': r'[\w\'"})\];]$',
            'space_right': r'^[\w\'"{(\[]',
            'connect_right': r'^[=+]',
        },
        {
            'syntax': ['xml', 'css', 'html.basic'],
            'space_left': r'[\'"})\];]$',
            'space_right': r'^[\'"{(\[]',
            'connect_right': r'^[=+]',
        },
    ],
    '-': [
        {
            # No space around = in keyword args
            'syntax': 'python',
            'scope': ['meta.function-call', 'meta.function.parameters'],
            'space_left': r'[+*/\w\'"})\],]$',
            'connect_right': r'^[-]',
        },
        {
            'syntax': ['xml', 'css', 'html.basic'],
            'space_left': r'[=\'"})\],]$', # not after \w
            'space_right': r'^[\'"{(\[]',
            'connect_right': r'^[-]',
        },
        {
            'syntax': ['tex.latex'],
            'space_left': r'[+*/=\'"})\],]$', # not \w
            'space_right': r'^[\'"{(\[]',
            'connect_right': r'^[-]',
        },
        {
            'scope': ['meta.item-access'],
            'space_left': r'[+*/=\'"},]$',
            'space_right': r'^[\'"{]',
            'connect_right': r'^[-]',
        },
        {
            'space_left': r'[+*/=\w\'"})\],]$',
            'space_right': r'^[\'"{(\[]',
            'connect_right': r'^[-]',
        },
    ],
    '*':
    [
        {
            'syntax': ['c', 'c++'],
            'space_left': r'[,\d=\'"})\]]$',
            'space_right': r'^[\w\'"{(\[]',
            'space_right_before': r'[\w\'"})\]]$',
            'connect_left': r'[{(\[]]$',
            'connect_right': r'^[\w=]',
            'connect_right_before': r'[^\w\'"})\]]$',
        },
        {
            'space_left': r'[,\w\'"})\]]$',
            'space_right': r'^[\w\'"{(\[]',
            'connect_right': r'^[=]',
            'ignore_scope': LatexIgnoreScopes,
        },
    ],
    '/': [
        {
            'space_left': r'[\w\'"})\]]$',
            'space_right': r'^[\w\'"{(\[]',
            'connect_right': r'^[=]',
        },
        {
            'syntax': ['xml', 'shell.bash', 'html.basic', 'tex.latex'],
            'space_left': r'[\'"})\]]$',
            'space_right': r'^[\'"{(\[]',
            'ignore_scope': LatexIgnoreScopes,
        },
    ],
    '^': {
        'space_left': r'[\w\'"})\]]$',
        'space_right': r'^[\w\'"{(\[]',
        'connect_right': r'^[=]',

        # 'space_left': r'[)\]]$',
        # 'connect_left': r'[\w]$',
        # 'space_right': r'^[a-zA-Z_(]',
        # 'connect_right': r'^[=0-9]',
    },
    '%':
    [
        {
            'syntax': ['xml', 'css', 'html.basic'],
            'space_left': r'[[a-zA-Z_]\'"})\]]$',
            'space_right': r'^[\w\'"{(\[]',
            'connect_right': r'^[=]',
        },
        {
            'space_left': r'[\w\'"})\]]$',
            'space_right': r'^[\w\'"{(\[]',
            'connect_right': r'^[=]',
        },
    ],
    '&': [
        {
            'syntax': ['c', 'c++'],
            'space_left': r'[,=\'"})\]]$', # not \w for references
            'space_right': r'^[\w\'"{(\[]',
            'space_right_before': r'[\w\'"})\]]$',
            'connect_right': r'^[=]',
            'connect_right_before': r'[^\w\'"})\]]$',
            'connect_left': r'[&]$',
        },
        {
            'space_left': r'[,=\w\'"})\]]$',
            'space_right': r'^[\w\'"{(\[]',
            'connect_right': r'^[\w=]',
            'connect_left': r'[&]$',
        },
    ],
    '|': {
        'space_left': r'[,=\w\'"})\]]$',
        'space_right': r'^[\w\'"{(\[]',
        'connect_right': r'^[=]',
    },
    '<': [
        {
            'syntax': ['xml', 'html.basic'],
            'space_left': r'[})\]]$',
            'space_right': r'^[{\[]',
            'connect_right': r'^[=]',
        },
        {
            'syntax': ['c', 'c++', 'java'],
            'space_left': r'[\'"})\]]$', # not for \w for templates
            'space_right': r'^[\'"{\[]', # not for \w and ( for templates
            'connect_right': r'^[=]',
        },
        {
            'space_left': r'[\w\'"})\]]$',
            'space_right': r'^[\w\'"{(\[]',
            'connect_right': r'^[=]',
        },
    ],
    '<s': [
        {
            'snippet': '<',
            'space_left': r'[\w\'"})\]]$',
            'space_right': r'^[\w\'"{(\[]',
            'connect_right': r'^[=]',
            'request_space_after': True
        },
    ],
    '>': [
        {
            'syntax': ['xml', 'html.basic'],
            'space_left': r'[})\]]$',
            'space_right': r'^[{\[]',
            'connect_right': r'^[=]',
        },
        {
            'syntax': ['c', 'c++', 'java'],
            'space_left': r'[\'"})\]]$', # not for \w for templates
            'space_right': r'^[\'"{\[]', # not \w for -> operator QQ, not for ( for templates
            'connect_right': r'^[=]',
        },
        {
            'space_left': r'[\w\'"})\]]$',
            'space_right': r'^[\w\'"{(\[]',
            'connect_right': r'^[=]',
        },
    ],
    '>s': [
        {
            'snippet': '>',
            'space_left': r'[\w\'"})\]]$',
            'space_right': r'^[\w\'"{(\[]',
            'connect_right': r'^[=]',
            'request_space_after': True
        },
    ],
    '@': {
        'space_left': r'[=]$',
    },
    '.': [
        {
            'syntax': ['php'],
            'space_left': r'.$',
            'space_right': r'^[^=\])}]',
        },
        {
            'syntax': 'matlab',
            'connect_right': r'^[^,]',
        },
        {
            'syntax': ['tex.latex'],
            'space_right': r'^[\w]',
            'ignore_scope': LatexIgnoreScopes,
        },
        {
            'connect_left': r'[^,]$',
            'connect_right': r'^[\a_]',
        },
    ],
    ',': [
        {
            'connect_left': r'.$',
            'space_right': r'^[^\])}>]',
            'no_space_keyword': True,
        },
    ],
    ':': [
        {
            'syntax': ['c', 'c++'],
            'space_left': r'[)}\]]$',
            'no_space_keyword': True,
        },
        {
            'syntax': ['xml', 'html.basic', 'matlab'],
        },
        {
            'space_right': r'^[^\])}]',
            'no_space_keyword': True,
        },
    ],
    '#': [
        {
            'syntax': ['tex.latex'],
            'ignore_scope': LatexIgnoreScopes,
        },
        {
            'space_left': r'.$',
            # 'space_right': r'^.',
        }
    ],
    '$': {
        'space_left': r'[;=+*/%|,.\w\'":})\]]$',
        'connect_right': r'^.',
    },
    '_': [
        {
            'syntax': 'python',
            'space_left': r'[-;=+*/%&^|~,\'":]$',
            'connect_right': r'^[:)\]}]',
        },
        {
            'syntax': ['c', 'c++'],
            'space_left': r'([-;=/&^|~,\'"]|[^:]:|[^+]\+|[\w\'"})\]][ \t]*[*&-])$', # fix for : vs ::, ++, --
            'connect_right': r'^[:)\]}]',
        },
        {
            'space_left': r'[-;=+*/%&^|~,\'"]$',
            'connect_right': r'^[:)\]}]',
        },
    ],
    'letter': [
        {
            # No space around : in slicing
            'syntax': 'python',
            'scope': ['meta.item-access'],
            'space_left': r'([;=+/%&^|,\'")\]}#<>]|[\w\'"})\]][ \t]*-|[^*]\*)$',
            'connect_right': r'^[:)]',
        },
        {
            # No space around = in keyword args
            'syntax': 'python',
            'scope': ['meta.function-call', 'meta.function.parameters'],
            'space_left': r'([;+/%&^|,\'":)\]}#<>]|[\w\'"})\]][ \t]*-|[^*]\*)$',
            'connect_right': r'^[:)]',
        },
        # Extra complexity for - to find out if user meant unary or not
        {
            'syntax': 'python',
            'space_left': r'([;=+/%&^|,\'":)\]}#<>]|[\w\'"})\]][ \t]*-|[^*]\*)$',
            'space_right': r'^[-=+*/%&^|\'"#<>]',
            'connect_right': r'^[:)]',
        },
        {
            'syntax': ['css'],
            'space_left': r'([;+*/%&|,:)\]}])$', # Not after ' " < > - #
            'connect_right': r'^[:)\]}]',
        },
        {
            'syntax': ['xml', 'shell', 'shell.bash', 'html.basic'],
            'space_left': r'([;,)\]}])$', # Not after ' " < > - # :
            'connect_right': r'^[:)\]}]',
        },
        # {
        #     'syntax': ['c', 'c++'],
        #     'scope': ['meta.method-call'],
        #     # not after # (for #inlude), and not after < for templates, and : vs ::, ->
        #     'space_left': r'([;=/%|^,\'")\]{}]|[&*\w\'"})\]][ \t]*[*&-]|[^-]>|[^:]:|[^+]\+)$',
        #     'connect_right': r'^[)\]]',
        #     # 'space_right': r'^[}]',
        # },
        {
            'syntax': ['c', 'c++'],
            # not after # (for #inlude), and not after < for templates, and : vs ::, ->
            'space_left': r'([?;=/%|^,\'")\]}]|[&*\w\'"})\]][ \t]*[*&-]|[^-]>|[^:]:|[^+]\+)$',
            'connect_right': r'^[)\]]',
            # 'space_right': r'^[}]',
        },
        {
            'syntax': ['tex.latex'],
            'space_left': r'[;=+!?,.:})\]]$',
            'connect_left': r'[{(\[]$',
            'connect_right': r'^[;!?,.:)\]}]',
            # 'caps_after': r'^$|[!?.]$|\\item$',
            # 'lower_after': r'[^!?.]$',
            'ignore_scope': LatexIgnoreScopes
        },
        {
            'syntax': ['java'],
            # not after < for templates
            'space_left': r'([;=+*/%&^|,:\'")\]}>]|[\w\'"})\]][ \t]*-)$', # not after # (for #inlude)
            'connect_right': r'^[:)\]}]',
        },
        {
            'syntax': ['lua'],
            'space_left': r'([;=+*/%&^|,\'")\]}<>]|[\w\'"})\]][ \t]*-)$', # not after # (for #inlude)
            'connect_right': r'^[:)\]}]',
        },
        {
            'space_left': r'([;=+*/%&^|,:\'")\]}<>]|[\w\'"})\]][ \t]*-)$', # not after # (for #inlude)
            'connect_right': r'^[:)\]}]',
        },
    ],
    'digit': [
        {
            # No space after : inside []
            'syntax': 'python',
            'scope': ['meta.item-access'],
            'space_left': r'([;=&^|\'")\]}#<>]|[\w\'"})\]][ \t]*-)$',
            'connect_right': r'[0-9:]',
        },
        {
            # No space around = in keyword args
            'syntax': 'python',
            'scope': ['meta.function-call', 'meta.function.parameters'],
            'space_left': r'([;+*/%&^|,\'":)\]}#<>]|[\w\'"})\]][ \t]*-)$',
            'connect_right': r'[0-9:\]}]',
        },
        {
            'syntax': 'matlab',
            'space_left': r'([;=+*/%&^|,\'")\]}#<>]|[\w\'"})\]][ \t]*-)$',
            'connect_right': r'[:)\]}]', # don't connect numbers in matlab
        },
        {
            'syntax': ['xml', 'shell', 'shell.bash', 'html.basic'],
            'space_left': r'[;=+*/%&|,\'":)\]}<>]$', # not after #
            'connect_right': r'[0-9:)\]}]',
        },
        {
            'syntax': ['tex.latex'],
            'space_left': r'[;=+!?`,\A-Za-z\'":})\]]$',
            'connect_left': r'[{(\[.]$',
            'connect_right': r'^[;!?,.:)\]}]',
            'ignore_scope': LatexIgnoreScopes,
        },
        {
            'scope': ['meta.item-access'],
            'space_left': r'([;=&^|,\'")\]}#<>])$',
            'connect_right': r'[0-9:)\]}]',
        },
        {
            'syntax': ['c', 'c++'],
            # not after # (for #inlude), and not after < for templates, and : vs ::, ->
            'space_left': r'([;=/%|^,\'")\]{}]|[&*\w\'"})\]][ \t]*[*&-]|[^-]>|[^:]:|[^+]\+)$',
            'space_left': r'([;=+*/%&^|,\'":)\]}#<>]|[\w\'"})\]][ \t]*-)$',
            'connect_right': r'^[)\]]',
            'space_right': r'^[}]',
        },
        {
            'space_left': r'([;=+*/%&^|,\'":)\]}#<>]|[\w\'"})\]][ \t]*-)$',
            'connect_right': r'[0-9:)\]}]',
        },
    ],
    'keyword': [
        {
            # No space around = in keyword args
            'syntax': 'python',
            'scope': ['meta.function-call', 'meta.function.parameters'],
            'space_left': r'[^=({[]$', # not after # (for #inlude)
            'space_right': r'^[^,;:)\]}]',
            'request_space_after': True
        },
        {
            'syntax': ['c', 'c++'],
            # 'scope': ['punctuation.section.generic.end.c++'],
            'space_left': r'[^({[<]$', # not after # (for #inlude)
            'space_right': r'^[^,;:)\]}>]',
            'request_space_after': True
        },
        {
            'space_left': r'[^({[]$', # not after # (for #inlude)
            'space_right': r'^[^,;:)\]}]',
            'request_space_after': True
        },
    ],
    'function': [
        {
            # No space around = in keyword args
            'syntax': 'python',
            'scope': 'meta.function-call',
            'space_left': r'[^=({[.~!]$', # not after # (for #inlude)
            'space_right': r'^[^()[\]{};.:,]',
        },
        {
            'syntax': 'python',
            'space_left': r'[^({[.~!]$', # not after # (for #inlude)
            'space_right': r'^[^()[\]{};.:,]',
        },
        {
            'syntax': ['c', 'c++'],
            'space_left': r'([^({[.~!>:]|[^-]>)$', # not after # (for #inlude), not after ->
            'space_right': r'^[^()[\]{};.:,]',
        },
        {
            'syntax': 'lua',
            'space_left': r'[^:({[.~!]$', # not after # (for #inlude)
            'space_right': r'^[^()[\]{};.:,]',
        },

    ],
    'method': [
        {
            'space_right': r'^[^()[\]{};.:,]',
            'connect_left': r'[\w)\]}_\']$',
        },
    ],
    ' ': [
        {
        }
    ],
}



def GetKeyForLookup(key):
    keyForLookup = key
    if not keyForLookup in CleverInsertKeys:
        if re.match('^[a-zA-Z]$', key): keyForLookup = 'letter'
        if re.match('^[0-9]$', key): keyForLookup = 'digit'
    return keyForLookup


def GetDataForKey(view, pos, keyForLookup, current_syntax):
    if keyForLookup not in CleverInsertKeys: return None

    data = CleverInsertKeys[keyForLookup]
    if isinstance(data, list):
        def data_score(data):
            score = 0

            if 'scope' in data:
                scopes = data['scope'] if isinstance(data['scope'], list) else [data['scope']]
                match = any(view.score_selector(pos, scope) and view.score_selector(pos - 1, scope) for scope in scopes)
                if not match: return -1

            if 'syntax' in data:
                if isinstance(data['syntax'], list) and current_syntax not in data['syntax']: return -1
                if isinstance(data['syntax'], str) and current_syntax != data['syntax']: return -1
                score += 1

            return score

        # pp([data_score(d) for d in data])

        return max(data, key=data_score)
    else:
        return data


def ResetJustInsertedSpace():
    global JustInsertedSpace
    JustInsertedSpace = False


def LastInsertedRequestsSpace(keyData, pos):
    global LastInsertedData
    return \
        LastInsertedData and LastInsertedData.get('request_space_after', False) \
        and pos == LastInsertedPoint and not keyData.get('no_space_keyword', False)


def ShouldHaveSpaceAfter(keyData, char_before, char_after):
    return \
        'space_right' in keyData and \
        re.search(keyData['space_right'], char_after) and \
        ('space_right_before' not in keyData or re.search(keyData['space_right_before'], char_before))


def ShouldHaveSpaceBefore(keyData, char_before, char_after, pos):
    return \
        'space_left' in keyData and \
        re.search(keyData['space_left'], char_before) and \
        ('space_left_after' not in keyData or re.match(keyData['space_left_after'], char_after)) or \
        LastInsertedRequestsSpace(keyData, pos)


def ShouldConnectAfter(keyData, char_before, char_after, space_after):
    return \
        space_after and '\n' not in space_after and \
        'connect_right' in keyData and \
        re.match(keyData['connect_right'], char_after) and \
        char_after and \
        ('connect_right_before' not in keyData or re.search(keyData['connect_right_before'], char_before))


def ShouldConnectBefore(keyData, char_before, char_after, space_before):
    return \
        space_before and '\n' not in space_before and \
        'connect_left' in keyData and \
        re.search(keyData['connect_left'], char_before) and \
        char_before and \
        ('connect_left_after' not in keyData or re.match(keyData['connect_left_after'], char_after))


def InsertString(key, keyData, view, edit, sel):
    global JustInsertedSpace, LastInsertedData, LastInsertedKey, LastInsertedPoint

    # grab text around us
    text_before = get_text_after(view, sel.begin(), False)
    text_after = get_text_after(view, sel.end(), True)
    char_before, space_before = split_text_before(text_before)
    char_after, space_after = split_text_after(text_after)


    # print("text_before:--%s--  text_after:--%s--" % (text_before, text_after))
    # print("space_before:--%s-- char_before:--%s--" % (space_before, char_before))
    # print("space_after:--%s-- char_after:--%s--" % (space_after, char_after))
    # pp(keyData)

    # print("Clever insert change caps: %s" % view.settings().get('CleverInsert_ChangeCaps', True))

    if view.settings().get('CleverInsert_ChangeCaps', True):
        if 'lower_after' in keyData and re.search(keyData['lower_after'], char_before):
            key = key.lower()

        if 'caps_after' in keyData and re.search(keyData['caps_after'], char_before):
            key = key.upper()

    # print('caps_after: %s' % keyData['caps_after'])
    # print('adding: %s' % key)

    # check right pattern
    add_space_after = ShouldHaveSpaceAfter(keyData, char_before, char_after) and not space_after

    if ShouldConnectAfter(keyData, char_before, char_after, space_after):
        point = view.find_by_class(sel.end(), True, sublime.CLASS_WORD_START | sublime.CLASS_PUNCTUATION_START)
        view.replace(edit, sublime.Region(sel.end(), point), '')


    # now check our left pattern
    add_space_before = ShouldHaveSpaceBefore(keyData, char_before, char_after, sel.end()) and not space_before
    
    if ShouldConnectBefore(keyData, char_before, char_after, space_before):
        point = view.find_by_class(sel.begin(), False, sublime.CLASS_WORD_END | sublime.CLASS_PUNCTUATION_END)
        view.replace(edit, sublime.Region(point, sel.begin()), '')

    # add key and spaces
    LastInsertedKey = key
    LastInsertedData = keyData

    if key == '$':
        key = r'\$';

    t = keyData.get('snippet', key)
    if add_space_before: t = ' ' + t

    LastInsertedPoint = sel.begin() + len(t)

    if '$0' not in t and '${' not in t:
        t += '$0'
    if add_space_after: t += ' '
    view.run_command('insert_snippet', args={"contents": t});

    if add_space_after:
        JustInsertedSpace = True
        sublime.set_timeout(ResetJustInsertedSpace, 1000)


    #print('LastInsertedPoint: %d' % LastInsertedPoint)
    #print('sel.end: %d' % sel.end())



def InsertSemicolon(view, edit, sel):
    global LastInsertedData, LastInsertedKey, LastInsertedPoint

    current_syntax = get_current_syntax(view, sel.end())
    keyData = GetDataForKey(view, sel.begin(), ';', current_syntax)

    atEnd = keyData.get('at_end', False)
    if atEnd:
        line_region = view.line(sel.end())
        line = view.substr(line_region)

        atEnd = line[-1:] != ';'
        # and line[-1:] != '}'

        if re.match(r'^\s*for\s*\(', line) and line.count(';') < 2:
            atEnd = False

    if atEnd:
        view.insert(edit, line_region.end(), ';')
        LastInsertedData = keyData
        LastInsertedKey = ';'
        LastInsertedPoint = line_region.end() + 1
    else:
        InsertString(';', keyData, view, edit, sel)

def InsertSpace(view, edit, sel):
    global JustInsertedSpace, LastInsertedData, LastInsertedKey, LastInsertedPoint

    if JustInsertedSpace:
        view.insert(edit, sel, ' ')
        LastInsertedData = None
        LastInsertedKey = ' '
        LastInsertedPoint = sel.end() + 1
    JustInsertedSpace = False



class CleverInsertKeywordCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        def on_done(keyword):
            global LastInsertedData, LastInsertedKey
            for region in self.view.sel():
                current_syntax = get_current_syntax(self.view, region.end())
                keyData = GetDataForKey(self.view, region.begin(), 'keyword', current_syntax)
                InsertString(keyword, keyData, self.view, edit, region)
                LastInsertedKey = 'keyword'
                break

        self.view.window().show_input_panel('Keyword:', '', on_done, None, None)


class CleverInsertFunctionCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        def on_done(function):
            global LastInsertedData, LastInsertedKey
            key_name = 'method' if re.match('^(\.|->|::|$|:|#)', function) else 'function'
            for region in self.view.sel():
                current_syntax = get_current_syntax(self.view, region.begin())
                keyData = GetDataForKey(self.view, region.begin(), key_name, current_syntax)
                # grab text around us
                char_after = self.view.substr(sublime.Region(region.end(), region.end() + 1))
                if char_after == '(':
                    function = re.sub(r'^[^a-zA-Z]*', '', function)
                    InsertString(function + '$0', keyData, self.view, edit, region)
                else:
                    InsertString(function + '(${0:$SELECTION})', keyData, self.view, edit, region)
                LastInsertedKey = 'function'
                LastInsertedData = keyData
                break

        self.view.window().show_input_panel('Function:', '', on_done, None, None)


class CleverInsertCommand(sublime_plugin.TextCommand):

    def run(self, edit, key):

        view = self.view

        keyForLookup = GetKeyForLookup(key)

        for region in self.view.sel():
            current_syntax = get_current_syntax(view, region.end())
    
            if keyForLookup == ';':
                keyfunc = InsertSemicolon
            elif keyForLookup == ' ':
                keyfunc = InsertSpace
            else:
                keyData = GetDataForKey(self.view, region.begin(), keyForLookup, current_syntax)
                if not keyData: return
                keyfunc = partial(InsertString, key, keyData)


            is_sel_empty = region.empty()
            # if is_sel_empty:
            keyfunc(self.view, edit, region)

                # if keyForLookup == 'letter':
                #   self.view.run_command('auto_complete', {
                #       'disable_auto_insert': True,
                #       # 'api_completions_only': True,
                #       'next_completion_if_showing': False,
                #       # 'auto_complete_commit_on_tab': True,
                #   })

                # break

            # print("snippet %s" % key)
            # view.run_command('insert_snippet', args={"contents": key});
            break

            # self.view.erase(edit, region)
            # self.view.insert(edit, region.begin(), key)
            # self.view.run_command('auto_complete', {
            #   'disable_auto_insert': True,
            #   # 'api_completions_only': True,
            #   'next_completion_if_showing': False,
            #   # 'auto_complete_commit_on_tab': True,
            # })



def supported(view, pos, keyData):
    if keyData is None:
        return False

    current_syntax = get_current_syntax(view, pos)
    if current_syntax in CleverInsertIgnoreSyntaxes:
        return False

    if view.score_selector(pos, 'string') and not view.score_selector(pos, 'punctuation.definition.string.begin'):
        return False

    if any(view.score_selector(pos, scope) for scope in CleverInsertIgnoreScopes):
        return False

    scope_name = view.scope_name(pos)
    if 'ignore_scope' in keyData and any(igs in scope_name for igs in keyData['ignore_scope']):
        return False

    return True


class CleverInsertListener(sublime_plugin.EventListener):

    def contextForSpaceAround(self, key, keyData, sel, view):
        global JustInsertedSpace, LastInsertedData, LastInsertedPoint

        # grab text around us
        text_before = get_text_after(view, sel.begin(), False)
        text_after = get_text_after(view, sel.end(), True)
        char_before, space_before = split_text_before(text_before)
        char_after, space_after = split_text_after(text_after)

        # print("text_before:--%s--" % text_before)
        # print("space_before:--%s-- char_before:--%s--" % (space_before, char_before))

        # print("Clever insert change caps: %s" % view.settings().get('CleverInsert_ChangeCaps', True))

        if view.settings().get('CleverInsert_ChangeCaps', True):
            if 'lower_after' in keyData and re.search(keyData['lower_after'], char_before) and key.isupper():
                return True

            if 'caps_after' in keyData and re.search(keyData['caps_after'], char_before) and key.islower():
                return True


        # print('LastInsertedPoint: %d' % LastInsertedPoint)
        # print('sel.end: %d' % sel.end())

        if ShouldHaveSpaceAfter(keyData, char_before, char_after) and not space_after:
            return True

        if ShouldConnectAfter(keyData, char_before, char_after, space_after):
            return True

        if ShouldHaveSpaceBefore(keyData, char_before, char_after, sel.end()) and not space_before:
            return True

        if ShouldConnectBefore(keyData, char_before, char_after, space_before):
            return True

        JustInsertedSpace = False
        return False



    def contextForSemi(self, sel, view):
        line_region = view.line(sel)
        line = view.substr(line_region)
        return line[-1:] != ';'


    def contextForSpace(self, sel, view):
        global JustInsertedSpace
        return JustInsertedSpace

    def on_deactivated(self, view):
        global LastInsertedData, LastInsertedPoint
        LastInsertedData = ''
        LastInsertedPoint = None

    # def on_modified(self, view):
        # JustInsertedSpace = False

    def on_query_context(self, view, key, operator, operand, match_all):
        global LastInsertedData, LastInsertedPoint

        if key == "CleverInsert":
            key = operand


            # check each selection point
            for region in view.sel():
                # is_sel_empty = region.empty()
                # if not is_sel_empty:
                #   return False

                # scope_name = view.scope_name(point)
                # print("scope_name: %s" % scope_name)

                current_syntax = get_current_syntax(view, region.end())

                keyForLookup = GetKeyForLookup(key)
                keyData = GetDataForKey(view, region.begin(), keyForLookup, current_syntax)
                if not keyData: return False

                if not supported(view, region.begin(), keyData):
                    # print("Not supported")
                    return False


                # Check key specific context
                if keyForLookup == ';':
                    keyfunc = self.contextForSemi
                elif keyForLookup == ' ':
                    keyfunc = self.contextForSpace
                else:
                    keyfunc = partial(self.contextForSpaceAround, key, keyData)

                if not keyfunc(region, view):
                    return False

            return True

        else:
            return None





    # def old_on_text_command(self, view, command_name, args):
    #   # print("on_text_command %s" % command_name)
    #   # print(command_name)
    #   # print(args)
    #   pass

    # def old_on_modified(self, view):
    #   (s, d, i) = view.command_history(0)
    #   # print("s:--%s-- i:--%i--" % (s, i))
    #   # print(d)

    #   if s != 'insert': return

    #   # print(d['characters'][-1:])

    #   self.settings = view.settings()
    #   self.tab_size = int(self.settings.get('tab_size', 4))

    #   cpc = CleverPasteCommand(view)

    #   key = d['characters'][-1:]
    #   keyForLookup = key
    #   if not keyForLookup in CleverInsertKeys:
    #       if re.match('^[a-zA-Z]$', key): keyForLookup = 'letter'
    #       if re.match('^[0-9]$', key): keyForLookup = 'digit'
    #   if not keyForLookup in CleverInsertKeys:
    #       return
    #   keyData = CleverInsertKeys[keyForLookup]


    #   for region in view.sel():
    #       is_sel_empty = region.empty()
    #       if not is_sel_empty:
    #           print("huh?")
    #           return

    #       p = region.begin()
    #       scope_name = view.scope_name(p)
    #       print(scope_name)
    #       if view.score_selector(p, 'string') and not view.score_selector(p, 'punctuation.definition.string.begin') or view.score_selector(p, 'comment'):
    #           return

    #       text_before = view.substr(sublime.Region(view.find_by_class(p - 1, False, sublime.CLASS_LINE_END)+1, p - 1))
    #       text_after = view.substr(sublime.Region(p, view.find_by_class(p, True, sublime.CLASS_LINE_START)-1))

    #       # split text before
    #       m = re.search(r'([^ \t]*)([ \t]*)$', text_before)
    #       if m:
    #           char_before = m.group(1)
    #           space_before = m.group(2)
    #       else:
    #           print("no match?? --%s--" % text_before)

    #       # split text after
    #       m = re.search(r'^([ \t]*)([^ \t]*)', text_after)
    #       if m:
    #           space_after = m.group(1)
    #           char_after = m.group(2)
    #       else:
    #           print("no match?? --%s--" % text_after)

    #       # print("space_before:--%s-- char_before:--%s--" % (space_before, char_before))
    #       # print("space_after:--%s-- char_after:--%s--" % (space_after, char_after))



    #       # add_space_before = 'space_left' in keyData and re.search(keyData['space_left'], char_before)
    #       # if add_space_before and char_before and not space_before:
    #       #   view.run_command('clever_insert', args={"pos": p - 1, "cmd": 'add_space'})
    #       #   p += 1

    #       # add_space_after = 'space_right' in keyData and re.search(keyData['space_right'], char_after)
    #       # if add_space_after and char_after and not space_after:
    #       #   view.run_command('clever_insert', args={"pos": p, "cmd": 'add_space'})

    #       connect_right = 'connect_right' in keyData and re.match(keyData['connect_right'], char_after);
    #       if connect_right and char_after and space_after:
    #           view.run_command('clever_insert', args={"pos": p, "cmd": "connect_right"})

    #       connect_left = 'connect_left' in keyData and re.search(keyData['connect_left'], char_before)
    #       if connect_left and char_before and space_before:
    #           view.run_command('clever_insert', args={'pos': p - 1, 'cmd': 'connect_left'})

    #       # TODO: change this to replace space with ' '
    #       # add_space_before = 'space_left' in keyData and re.search(keyData['space_left'], char_before)
    #       # if add_space_before and char_before and space_before and space_before != ' ':
    #       #   view.run_command('clever_insert', args={"pos": p - 1, "cmd": 'add_space'})
    #       #   p += 1


    #       # print("text_after: --%s--  add_space_after: %d" %  (text_after, add_space_after != None))


# class CleverInsertCommandNew(sublime_plugin.TextCommand):
#   def run(self, edit, pos, cmd):
#       view = self.view

#       if cmd == 'add_space':
#           view.insert(edit, pos, ' ')
#       elif cmd == 'connect_right':
#           p2 = view.find_by_class(pos, True, sublime.CLASS_WORD_START | sublime.CLASS_PUNCTUATION_START)
#           view.replace(edit, sublime.Region(pos, p2), '')
#       elif cmd == 'connect_left':
#           p2 = view.find_by_class(pos, False, sublime.CLASS_WORD_END | sublime.CLASS_PUNCTUATION_END)
#           view.replace(edit, sublime.Region(p2, pos), '')
