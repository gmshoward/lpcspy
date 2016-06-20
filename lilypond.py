import ply.lexer as lex
import csound

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

tokens = (
    A,
    AA,
    N,
    ANY_CHAR,
    WORD,
    COMMAND,
    # SPECIAL category is for every letter that needs to get passed to
    # the parser rather than being redefinable by the user
    SPECIAL,
    SHORTHAND,
    UNSIGNED,
    E_UNSIGNED,
    FRACTION,
    INT,
    REAL,
    STRICTREAL,
    WHITE,
    HORIZONTALWHITE,
    BLACK,
    RESTNAME,
    ESCAPED,
    EXTENDER,
    HYPHEN
)

t_A = r'[a-zA-Z\200-\377]'
t_AA = r'{A}|_'
t_N = r'[0-9]'
t_ANY_CHAR = r'(.|\n)'
t_WORD = r'{A}([-_]{A}|{A})*'
t_COMMAND = r'\\{WORD}'
t_SPECIAL = r'[-+*/=<>{}!?_^'',.:]'
t_SHORTHAND = r'(.|\\.)'
t_UNSIGNED = r'{N}+'
t_E_UNSIGNED = r'\\{N}+'
t_FRACTION = r'{N}+\/{N}+'
t_INT = r'-?{UNSIGNED}'
t_REAL = r'({INT}\.{N}*)|(-?\.{N}+)'
t_STRICTREAL = r'{UNSIGNED}\.{UNSIGNED}'
t_WHITE = r'[ \n\t\f\r]'
t_HORIZONTALWHITE = r'[ \t]'
t_BLACK = r'[^ \n\t\f\r]'
t_RESTNAME = r'[rs]'
t_ESCAPED = r'[nt\\''""]'
t_EXTENDER = r'__'
t_HYPHEN = r'--'

def t_ANY_newline(t):
    r'\n'
    pass # swallow and ignore carriage returns

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

def t_version_Quote(t):
    r'\"[^""]*\"'
    pass # don't care about the LilyPond source version

def t_sourcefilename_Quote(t):
    r'\"[^""]*\"'
    # not sure we care about the sourcefilename either but save it anyhow
    t.lexer.sourcefilename = t.value()
    
def t_sourcefileline_Quote(t):
    r'\"[^""]*\"'
    # not sure we care about the sourcefilename either but save it anyhow
    t.lexer.sourcefileline = t.value()
    