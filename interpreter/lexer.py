import re
from interpreter.errors import LexerError

KEYWORDS = {
    'func', 'class', 'if', 'elif', 'else', 'for', 'while', 'return', 'say',
    'in', 'and', 'or', 'not', 'null', 'true', 'false', 'self', 'import',
    'try', 'catch', 'repeat', 'times', 'switch', 'case', 'default',
    'break', 'continue',
    'test', 'expect', 'to_be', 'to_be_true', 'to_be_false', 'to_throw',
    # GUI keywords (soft — usable as identifiers in normal code)
    'window', 'label', 'button', 'input', 'image', 'textbox',
    'checkbox', 'dropdown', 'options',
    'at', 'width', 'height', 'color', 'font_size', 'id',
    'on_click', 'on_change', 'on_key', 'placeholder', 'password',
    'set_text', 'to', 'get_text', 'show_window',
    'alert', 'set_color', 'set_visible', 'resizable',
    'text',
    # Creative / canvas keywords
    'canvas', 'draw', 'on', 'with', 'clear_canvas', 'slider',
    'progress', 'set_progress', 'every', 'after', 'call',
    'milliseconds', 'ms', 'second', 'seconds', 'beep', 'fill',
    'from', 'size',
}

# Words that are GUI syntax but may also be used as ordinary identifiers.
# The parser treats these as identifiers whenever they appear where a value
# is expected, so `text = "hi"` works while `label text "hi" at 0 0` still does.
SOFT_KEYWORD_TYPES = {
    'AT', 'WIDTH', 'HEIGHT', 'COLOR', 'FONT_SIZE', 'ID', 'OPTIONS',
    'PLACEHOLDER', 'PASSWORD', 'TEXT', 'RESIZABLE', 'TO', 'ON_CLICK',
    'ON_CHANGE', 'ON_KEY',
    'CANVAS', 'DRAW', 'ON', 'WITH', 'CLEAR_CANVAS', 'SLIDER',
    'PROGRESS', 'SET_PROGRESS', 'EVERY', 'AFTER', 'CALL', 'MILLIS',
    'SECONDS', 'BEEP', 'FILL', 'FROM', 'SIZE',
}

COMPARISON_OPS = {
    'is greater than or equal to': 'IS_GREATER_EQUAL',
    'is less than or equal to': 'IS_LESS_EQUAL',
    'is greater than': 'IS_GREATER_THAN',
    'is less than': 'IS_LESS_THAN',
    'is equal to': 'IS_EQUAL_TO',
    'is not equal to': 'IS_NOT',
    'is not': 'IS_NOT',
    'is': 'IS',
    '>=': 'IS_GREATER_EQUAL',
    '<=': 'IS_LESS_EQUAL',
    '>': 'IS_GREATER_THAN',
    '<': 'IS_LESS_THAN',
    '==': 'IS_EQUAL_TO',
    '!=': 'IS_NOT',
}


class Token:
    def __init__(self, type, value=None, line=None, column=None):
        self.type = type
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        if self.value is not None:
            return f"Token({self.type}, {repr(self.value)})"
        return f"Token({self.type})"


class Lexer:
    def __init__(self, source):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens = []
        self.indents = [0]
        self.bracket_depth = 0

    def peek(self, offset=0):
        idx = self.pos + offset
        if idx < len(self.source):
            return self.source[idx]
        return ''

    def advance(self):
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def skip_whitespace(self):
        while self.pos < len(self.source) and self.source[self.pos] in ' \t\r':
            self.advance()

    def skip_comment(self):
        while self.pos < len(self.source) and self.source[self.pos] != '\n':
            self.advance()

    def read_string(self):
        quote = self.peek()
        self.advance()
        parts = []
        buf = []
        while self.pos < len(self.source):
            ch = self.peek()
            if ch == '\\' and self.pos + 1 < len(self.source):
                nxt = self.peek(1)
                if nxt == 'n':
                    buf.append('\n')
                elif nxt == 't':
                    buf.append('\t')
                elif nxt == '\\':
                    buf.append('\\')
                elif nxt == quote:
                    buf.append(quote)
                else:
                    buf.append(nxt)
                self.advance()
                self.advance()
                continue
            if ch == quote:
                break
            buf.append(ch)
            self.advance()
        if self.pos >= len(self.source):
            raise LexerError(f"Unterminated string", line=self.line, column=self.column)
        self.advance()
        return ''.join(buf)

    def read_number(self):
        start = self.pos
        has_dot = False
        while self.pos < len(self.source) and (self.source[self.pos].isdigit() or self.source[self.pos] == '.'):
            if self.source[self.pos] == '.':
                if has_dot:
                    raise LexerError(f"Invalid number format", line=self.line, column=self.column)
                has_dot = True
            self.advance()
        value = self.source[start:self.pos]
        if has_dot:
            return float(value)
        return int(value)

    def read_identifier(self):
        start = self.pos
        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == '_'):
            self.advance()
        return self.source[start:self.pos]

    def check_keywords(self, word):
        word_lower = word.lower()
        if word_lower in KEYWORDS:
            return word_lower.upper()
        return 'IDENT'

    def handle_indentation(self):
        while self.peek() == '\n':
            self.advance()
        # If we've reached the end of the source, there's nothing to indent
        if self.peek() == '':
            return
        spaces = 0
        while self.peek() in ' \t':
            if self.peek() == ' ':
                spaces += 1
            elif self.peek() == '\t':
                spaces += 4
            self.advance()
        if self.peek() in ('\n', '#', ''):
            return
        current_indent = spaces // 4
        if spaces % 4 != 0:
            raise LexerError(f"Invalid indentation: use 4 spaces", line=self.line, column=self.column)
        if current_indent > self.indents[-1]:
            # Emit one INDENT per level so nested blocks parse correctly
            for _ in range(current_indent - self.indents[-1]):
                self.tokens.append(Token('INDENT', line=self.line, column=self.column))
            self.indents.append(current_indent)
        elif current_indent < self.indents[-1]:
            while self.indents[-1] > current_indent:
                self.tokens.append(Token('DEDENT', line=self.line, column=self.column))
                self.indents.pop()
            if self.indents[-1] != current_indent:
                raise LexerError(
                    f"Inconsistent indentation",
                    line=self.line, column=self.column,
                    suggestion="This line doesn't line up with any enclosing block"
                )

    def tokenize(self):
        COMPARISON_KEYWORDS = sorted(COMPARISON_OPS.keys(), key=len, reverse=True)

        single_tokens = {
            '+': 'PLUS', '-': 'MINUS', '*': 'MULT', '/': 'DIV', '%': 'MOD',
            '^': 'POW',
            '=': 'ASSIGN', '(': 'LPAREN', ')': 'RPAREN',
            '[': 'LBRACKET', ']': 'RBRACKET', '{': 'LBRACE',
            '}': 'RBRACE', '.': 'DOT', ',': 'COMMA', ':': 'COLON'
        }
        compound_tokens = {
            '+=': 'PLUS_ASSIGN', '-=': 'MINUS_ASSIGN',
            '*=': 'MULT_ASSIGN', '/=': 'DIV_ASSIGN', '%=': 'MOD_ASSIGN',
        }

        at_line_start = True
        while self.pos < len(self.source):
            if not at_line_start:
                self.skip_whitespace()
            if self.pos >= len(self.source):
                break

            ch = self.peek()

            if ch == '\n':
                self.advance()
                if self.bracket_depth > 0:
                    # Inside (...) / [...] / {...}: ignore newlines entirely
                    continue
                if self.tokens and self.tokens[-1].type not in ('NEWLINE', 'INDENT', 'DEDENT', 'COLON'):
                    self.tokens.append(Token('NEWLINE', line=self.line, column=self.column))
                self.handle_indentation()
                at_line_start = True
                continue

            at_line_start = False

            if ch == '#' or (ch == '/' and self.peek(1) == '/'):
                self.skip_comment()
                continue

            if self.peek() in ' \t\r':
                self.skip_whitespace()
                continue

            if ch.isdigit():
                value = self.read_number()
                self.tokens.append(Token('NUMBER', value, self.line, self.column))
                continue

            if ch in '"\'':
                value = self.read_string()
                self.tokens.append(Token('STRING', value, self.line, self.column))
                continue

            matched_comparison = False
            remaining_source = self.source[self.pos:]
            for kw in COMPARISON_KEYWORDS:
                if remaining_source.startswith(kw):
                    after_kw = remaining_source[len(kw):] if len(remaining_source) > len(kw) else ''
                    # Only enforce word boundary for text-based keywords (ending with a letter)
                    if not kw[-1].isalpha() or not after_kw or not after_kw[0].isalnum():
                        self.tokens.append(Token(COMPARISON_OPS[kw], kw, self.line, self.column))
                        for _ in range(len(kw)):
                            self.advance()
                        matched_comparison = True
                        break
            if matched_comparison:
                continue

            if ch.isalpha() or ch == '_':
                word = self.read_identifier()
                token_type = self.check_keywords(word)
                self.tokens.append(Token(token_type, word, self.line, self.column))
                continue

            two_char = self.source[self.pos:self.pos + 2]
            if two_char in compound_tokens:
                self.tokens.append(Token(compound_tokens[two_char], two_char, self.line, self.column))
                self.advance()
                self.advance()
                continue

            if ch in single_tokens:
                ttype = single_tokens[ch]
                if ttype in ('LPAREN', 'LBRACKET', 'LBRACE'):
                    self.bracket_depth += 1
                elif ttype in ('RPAREN', 'RBRACKET', 'RBRACE'):
                    self.bracket_depth = max(0, self.bracket_depth - 1)
                self.tokens.append(Token(ttype, ch, self.line, self.column))
                self.advance()
                continue

            raise LexerError(f"Unexpected character '{ch}'", line=self.line, column=self.column)

        while self.indents[-1] > 0:
            self.tokens.append(Token('DEDENT', line=self.line, column=self.column))
            self.indents.pop()

        self.tokens.append(Token('EOF', line=self.line, column=self.column))
        return self.tokens
