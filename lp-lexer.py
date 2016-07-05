from __future__ import print_function
import ply.lexer as lex
from ply.lex import TOKEN
import csound
import codecs
import sys

states = (
    ('chords', 'exclusive'),
    ('figures', 'exclusive'),
    ('incl', 'exclusive'),
    ('lyrics', 'exclusive'),
    ('longcomment', 'exclusive'),
    ('maininput', 'exclusive'),
    ('markup', 'exclusive'),
    ('notes', 'exclusive'),
    ('quote', 'exclusive'),
    ('commandquote', 'exclusive'),
    ('sourcefileline', 'exclusive'),
    ('sourcefilename', 'exclusive'),
    ('version', 'exclusive')
)

# SPECIAL category is for every letter that needs to get passed to
# the parser rather than being redefinable by the user
tokens = (
    "A",
    "AA",
    "N",
    "ANY_CHAR",
    "WORD",
    "COMMAND",
    "SPECIAL",
    "SHORTHAND",
    "UNSIGNED",
    "E_UNSIGNED",
    "FRACTION",
    "INT",
    "REAL",
    "STRICTREAL",
    "WHITE",
    "HORIZONTALWHITE",
    "BLACK",
    "RESTNAME",
    "ESCAPED",
    "EXTENDER",
    "HYPHEN",
    "BOM_UTF8"
)

t_A = r'[a-zA-Z\200-\377]'
t_AA = t_A + r'|_'
t_N = r'[0-9]'
t_ANY_CHAR = r'(.|\n)'
t_WORD = t_A + r'([-_]' + t_A + r'|' + t_A + r')*'
t_COMMAND = r'\\' + t_WORD
t_SHORTHAND = r'(.|\\.)'
t_UNSIGNED = t_N + r'+'
t_E_UNSIGNED = r'\\' + t_N + '+'
t_FRACTION = t_N + r'+\/' + t_N + r'+'
t_INT = r'-?' + t_UNSIGNED
t_REAL = r'(' + t_INT + r'\.' + t_N + r'*)|(-?\.' + t_N + r'+)'
t_STRICTREAL = t_UNSIGNED + r'\.' + t_UNSIGNED
t_WHITE = r'[ \n\t\f\r]'
t_HORIZONTALWHITE = r'[ \t]'
t_BLACK = r'[^ \n\t\f\r]'
t_RESTNAME = r'[rs]'
t_ESCAPED = r'[nt\\''""]'
t_EXTENDER = r'__'
t_HYPHEN = r'--'
t_BOM_UTF8 = codecs.BOM_UTF8


def t_ANY_newline(t):
    r'\n'
    pass  # swallow and ignore carriage returns


def t_INITIAL_chords_figures_incl_lyrics_markup_notes_StartMLComment(t):
    r'%{'
    t.lexer.push_state('longcomment')


def t_INITIAL_chords_figures_incl_lyrics_markup_notes_PercentNobrace(t):
    r'%[^{\n\r][^\n\r]*[\n\r]?'
    return t


def t_INITIAL_chords_figures_incl_lyrics_markup_notes_PercentCRLF(t):
    r'%[\n\r]?'
    pass


def t_INITIAL_chords_figures_incl_lyrics_markup_notes_Whitespace(t):
    r'\s+'
    pass


def t_INITIAL_chords_figures_markup_notes_StartQuote(t):
    r'"'
    t.lexer.push_state('quote')
    # (*lexval_) = SCM_EOL


def t_INITIAL_chords_figures_lyrics_notes_BackslashVersion(t):
    r'\\version\s*'
    t.lexer.push_state('version')


def t_INITIAL_chords_figures_lyrics_notes_BackslashSourcefilename(t):
    r'\\sourcefilename\s*'
    t.lexer.push_state('sourcefilename')


def t_INITIAL_chords_figures_lyrics_notes_BackslashSourcefileline(t):
    r'\\sourcefileline\s*'
    t.lexer.push_state('sourcefileline')


def extract_from_quotes(quoted_string):
    return quoted_string[1:quoted_string.rfind('"')]


def t_version_Quote(t):
    r'\"[^""]*\"'
    t.lexer.lpversion = extract_from_quotes(t.value())
    t.lexer.pop_state()


def t_sourcefilename_Quote(t):
    r'\"[^""]*\"'
    t.lexer.sourcefilename = extract_from_quotes(t.value())
    t.lexer.pop_state()


@TOKEN(t_INT)
def t_sourcefileline_INT(t):
    t.lexer.sourcefileline = int(t.value())
    t.lexer.pop_state()


@TOKEN(t_ANY_CHAR)
def t_version_sourcefilename_ANY_CHAR(t):
    print ("error: quoted string expected after \\[version,sourcefilename]", file=sys.stderr)
    t.lexer.pop_state()


@TOKEN(t_ANY_CHAR)
def t_version_sourcefileline_ANY_CHAR(t):
    print ("error: integer expected after \\sourcefileline", file=sys.stderr)
    t.lexer.pop_state()


def t_longcomment_NotBackslashOrPercent(t):
    r'[^\%]*'
    pass  # do nothing I guess?


def t_longcomment_PercentThenNotRightBraceOrPercent(t):
    r'\%*[^}%]*'
    pass  # do nothing I guess?


def t_longcomment_CommentEnd(t):
    r'%}'
    t.lexer.pop_state()


def t_INITIAL_chords_lyrics_notes_figures_BackslashMaininput(t):
    r'\\maininput'
    # start_main_input()  # not sure what this is supposed to do
    if not t.lexer.is_main_input_:
        t.lexer.main_input_level_ = len(t.lexer.include_stack_)
        t.lexer.is_main_input_ = True
    else:
        print("\\maininput not allowed outside init files", file=sys.stderr)


def t_INITIAL_chords_lyrics_figures_notes_BackslashInclude(t):
    r'\\include'
    t.lexer.push_state('include')


def t_include_QuotedFilename(t):
    r'\"[^""]*\"'
    s = extract_from_quotes(t.value())
    # new_input(s, sources_)
    t.lexer.pop_state()


# ...several more include-related functions I don't know how to support yet...


def t_include_version_sourcefilename_EndQuoteMissing(t):
    r'\"[^""]*'
    print("end quote missing", file=sys.stderr)
