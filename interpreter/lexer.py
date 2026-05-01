import re
from interpreter.errors import LexerError

KEYWORDS = {
    'func', 'class', 'if', 'elif', 'else', 'for', 'while', 'return', 'say',
    'in', 'and', 'or', 'not', 'null', 'true', 'false', 'self', 'import',
    'try', 'catch',
    # GUI keywords
    'window', 'label', 'button', 'input', 'image', 'textbox',
    'checkbox', 'dropdown', 'options',
    'at', 'width', 'height', 'color', 'font_size', 'id',
    'on_click', 'on_change', 'placeholder', 'password',
    'set_text', 'to', 'get_text', 'show_window',
    'alert', 'set_color', 'set_visible', 'resizable',
    'text',
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

TOKEN_TYPES = {
    'PLUS': '+',
    'MINUS': '-',
    'MULT': '*',
    'DIV': '/',
    'ASSIGN': '=',
    'LPAREN': '(',
    'RPAREN': ')',
    'LBRACKET': '[',
    'RBRACKET': ']',
    'LBRACE': '{',
    'RBRACE': '}',
    'DOT': '.',
    'COMMA': ',',
    'COLON': ':',
    'NEWLINE': 'NEWLINE',
    'INDENT': 'INDENT',
    'DEDENT': 'DEDENT',
    'EOF': 'EOF',
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
        start = self.pos
        while self.pos < len(self.source) and self.source[self.pos] != quote:
            if self.source[self.pos] == '\\' and self.pos + 1 < len(self.source):
                self.advance()
            self.advance()
        if self.pos >= len(self.source):
            raise LexerError(f"Unterminated string", line=self.line, column=self.column)
        value = self.source[start:self.pos]
        self.advance()
        return value

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
            # If we've reached the end while counting spaces, break
            if self.peek() == '':
                break
        if self.peek() == '\n' or self.peek() == '#' or self.peek() == '':
            return
        current_indent = spaces // 4
        if spaces % 4 != 0:
            raise LexerError(f"Invalid indentation: use 4 spaces", line=self.line, column=self.column)
        if current_indent > self.indents[-1]:
            self.tokens.append(Token('INDENT', line=self.line, column=self.column))
            self.indents.append(current_indent)
        elif current_indent < self.indents[-1]:
            while self.indents[-1] > current_indent:
                self.tokens.append(Token('DEDENT', line=self.line, column=self.column))
                self.indents.pop()

    def tokenize(self):
        COMPARISON_KEYWORDS = sorted(COMPARISON_OPS.keys(), key=len, reverse=True)

        while self.pos < len(self.source):
            self.skip_whitespace()
            if self.pos >= len(self.source):
                break

            ch = self.peek()

            if ch == '\n':
                self.advance()
                if self.tokens and self.tokens[-1].type not in ('NEWLINE', 'INDENT', 'DEDENT', 'COLON'):
                    self.tokens.append(Token('NEWLINE', line=self.line, column=self.column))
                self.handle_indentation()
                continue

            if ch == '#' or (ch == '/' and self.peek(1) == '/'):
                self.skip_comment()
                continue

            if self.peek() in ' \t':
                self.skip_whitespace()
                self.handle_indentation()
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

            single_tokens = {
                '+': 'PLUS', '-': 'MINUS', '*': 'MULT', '/': 'DIV',
                '=': 'ASSIGN', '(': 'LPAREN', ')': 'RPAREN',
                '[': 'LBRACKET', ']': 'RBRACKET', '{': 'LBRACE',
                '}': 'RBRACE', '.': 'DOT', ',': 'COMMA', ':': 'COLON'
            }

            if ch in single_tokens:
                self.tokens.append(Token(single_tokens[ch], ch, self.line, self.column))
                self.advance()
                continue

            raise LexerError(f"Unexpected character '{ch}'", line=self.line, column=self.column)

        while self.indents[-1] > 0:
            self.tokens.append(Token('DEDENT', line=self.line, column=self.column))
            self.indents.pop()

        self.tokens.append(Token('EOF', line=self.line, column=self.column))
        return self.tokens