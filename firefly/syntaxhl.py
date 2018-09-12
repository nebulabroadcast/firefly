from .common import *

def format(color, style=''):
    _color = QColor(color)
    #_color.setNamedColor(color)
    _format = QTextCharFormat()
    _format.setForeground(_color)
    if 'bold' in style:
        _format.setFontWeight(QFont.Bold)
    if 'italic' in style:
        _format.setFontItalic(True)
    return _format

STYLES = {
    'keyword'  : format('#f92672','bold'),
    'operator' : format('#f92672'),
    'brace'    : format('#f8f8f2'),
    'defname'  : format('#a6e22e'),
    'classname': format('#f8f8f2'),
    'cdefs'    : format('#66D9EF', 'italic'),
    'string'   : format('#E6DB74'),
    'string2'  : format('#E6DB74'),
    'comment'  : format('#75715E', 'italic'),
    'pybang'   : format('#75715E', 'italic'),
    'number'   : format('#AE81FF')
}





class PythonHL (QSyntaxHighlighter):
    keywords = ['and', 'as', 'assert', 'break', 'continue', 'del', 'elif', 'else', 'except', 'exec', 'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'not', 'or', 'pass', 'print', 'raise', 'return', 'try', 'while', 'with', 'yield', 'True', 'False', 'None' ]
    cdefs = ['def', 'class']
    operators = ['=','==', '!=', '<', '<=', '>', '>=','\+', '-', '\*', '/', '//', '\%', '\*\*','\+=', '-=', '\*=', '/=', '\%=','\^', '\|', '\&', '\~', '>>', '<<' ]
    braces = ['\{', '\}', '\(', '\)', '\[', '\]' ]

    def __init__(self, document):
        QSyntaxHighlighter.__init__(self, document)
        self.tri_single = (QRegExp("'''"), 1, STYLES['string2'])
        self.tri_double = (QRegExp('"""'), 2, STYLES['string2'])
        rules = []
        rules += [(r'\b%s\b' % w, 0, STYLES['keyword']) for w in PythonHL.keywords]
        rules += [(r'\b%s\b' % w, 0, STYLES['cdefs'])   for w in PythonHL.cdefs]
        rules += [(r'%s' % o, 0, STYLES['operator'])    for o in PythonHL.operators]
        rules += [(r'%s' % b, 0, STYLES['brace'])       for b in PythonHL.braces]
        rules += [(r'"[^"\\]*(\\.[^"\\]*)*"', 0, STYLES['string']),
                  (r"'[^'\\]*(\\.[^'\\]*)*'", 0, STYLES['string']),
                  (r'\bdef\b\s*(\w+)', 1, STYLES['defname']),
                  (r'\bclass\b\s*(\w+)', 1, STYLES['classname']),
                  (r'#[^\n]*', 0, STYLES['comment']),
                  (r'#![^\n]*', 0, STYLES['pybang']),
                  (r'[0-9]', 0, STYLES['number'])
                  ]
        self.rules = [(QRegExp(pat), index, fmt) for (pat, index, fmt) in rules]

    def highlightBlock(self, text):
        for expression, nth, format in self.rules:
            index = expression.indexIn(text, 0)
            while index >= 0:
                index = expression.pos(nth)
                length = len(expression.cap(nth))
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)
        self.setCurrentBlockState(0)
        in_multiline = self.match_multiline(text, *self.tri_single)
        if not in_multiline: in_multiline = self.match_multiline(text, *self.tri_double)


    def match_multiline(self, text, delimiter, in_state, style):
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        else:
            start = delimiter.indexIn(text)
            add = delimiter.matchedLength()
        while start >= 0:
            end = delimiter.indexIn(text, start + add)
            if end >= add:
                length = end - start + add + delimiter.matchedLength()
                self.setCurrentBlockState(0)
            else:
                self.setCurrentBlockState(in_state)
                length = len(text) - start + add
            self.setFormat(start, length, style)
            start = delimiter.indexIn(text, start + length)
        if self.currentBlockState() == in_state:  return True
        else: return False




