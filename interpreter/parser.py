from interpreter.nodes import *
from interpreter.errors import ParserError
from interpreter.lexer import SOFT_KEYWORD_TYPES

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self, offset=0):
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return None

    def advance(self):
        token = self.peek()
        self.pos += 1
        return token

    @staticmethod
    def _describe(token):
        """Human-friendly name for a token in error messages."""
        if token is None:
            return "end of file"
        names = {
            'NEWLINE': 'end of line',
            'DEDENT': 'end of block',
            'INDENT': 'start of an indented block',
            'EOF': 'end of file',
        }
        if token.value is not None:
            return f"'{token.value}'"
        return names.get(token.type, token.type)

    @staticmethod
    def _mark(node, token):
        """Attach source position to a node (first marking wins)."""
        if node is not None and getattr(node, 'line', None) is None \
                and token is not None and token.line is not None:
            node.line = token.line
            node.column = token.column
        return node

    def expect(self, token_type, suggestion=None):
        token = self.peek()
        if token is None or token.type != token_type:
            raise ParserError(
                f"I expected '{token_type}' here",
                line=token.line if token else None,
                column=token.column if token else None,
                suggestion=suggestion
            )
        return self.advance()

    def parse(self):
        statements = []
        while self.peek() and self.peek().type != 'EOF':
            if self.peek().type == 'NEWLINE':
                self.advance()
                continue
            start = self.peek()
            stmt = self._mark(self.parse_statement(), start)
            statements.append(stmt)
        return Program(statements)

    def parse_name(self, what="name", allow_soft=True):
        """Consume an identifier (soft GUI keywords allowed as names)."""
        token = self.peek()
        if token is None:
            raise ParserError(f"I expected a {what} here", suggestion=None)
        if token.type == 'IDENT' or (allow_soft and token.type in SOFT_KEYWORD_TYPES) \
                or token.type in ('WINDOW', 'LABEL', 'BUTTON', 'IMAGE', 'TEXTBOX',
                                  'CHECKBOX', 'DROPDOWN', 'ALERT', 'INPUT', 'GET_TEXT',
                                  'SET_TEXT', 'SET_COLOR', 'SET_VISIBLE', 'SHOW_WINDOW'):
            self.advance()
            if token.type == 'IDENT':
                return token.value
            return str(token.value).lower()
        raise ParserError(
            f"I expected a {what} here but found {self._describe(token)}",
            line=token.line, column=token.column,
            suggestion="pick a different " + what
        )

    def parse_statement(self):
        token = self.peek()

        if token.type == 'FUNC':
            return self.parse_func_def()
        elif token.type == 'CLASS':
            return self.parse_class_def()
        elif token.type == 'IF':
            return self.parse_if()
        elif token.type == 'FOR':
            return self.parse_for()
        elif token.type == 'WHILE':
            return self.parse_while()
        elif token.type == 'REPEAT':
            return self.parse_repeat()
        elif token.type == 'SWITCH':
            return self.parse_switch()
        elif token.type == 'BREAK':
            self.advance()
            return BreakStmt()
        elif token.type == 'CONTINUE':
            self.advance()
            return ContinueStmt()
        elif token.type == 'TRY':
            return self.parse_try_catch()
        elif token.type == 'RETURN':
            return self.parse_return()
        elif token.type == 'IMPORT':
            return self.parse_import()
        elif token.type == 'SAY':
            return self.parse_say()
        # GUI statements
        elif token.type == 'WINDOW':
            return self.parse_window()
        elif token.type == 'LABEL':
            return self.parse_label()
        elif token.type == 'BUTTON':
            return self.parse_button()
        elif token.type == 'INPUT':
            # `input` at statement level: widget OR console input expression
            nxt = self.peek(1)
            if nxt and nxt.type in ({'STRING', 'IDENT'} | SOFT_KEYWORD_TYPES):
                return self.parse_input_widget()
            return self.parse_expr_statement()
        elif token.type == 'IMAGE':
            return self.parse_image()
        elif token.type == 'TEXTBOX':
            return self.parse_textbox()
        elif token.type == 'CHECKBOX':
            return self.parse_checkbox()
        elif token.type == 'DROPDOWN':
            return self.parse_dropdown()
        elif token.type == 'SET_TEXT':
            return self.parse_set_text()
        elif token.type == 'SET_COLOR':
            return self.parse_set_color()
        elif token.type == 'SET_VISIBLE':
            return self.parse_set_visible()
        elif token.type == 'SHOW_WINDOW':
            return self.parse_show_window()
        elif token.type == 'ALERT':
            return self.parse_alert()
        # Creative / canvas statements
        elif token.type == 'CANVAS':
            if self._looks_like_widget():
                return self.parse_canvas_widget()
            return self.parse_expr_statement()
        elif token.type == 'DRAW':
            return self.parse_draw()
        elif token.type == 'CLEAR_CANVAS':
            self.advance()
            cid = self.parse_expression()
            return ClearCanvasStmt(cid)
        elif token.type == 'SLIDER':
            if self._looks_like_widget():
                return self.parse_slider_widget()
            return self.parse_expr_statement()
        elif token.type == 'PROGRESS':
            if self._looks_like_widget():
                return self.parse_progress_widget()
            return self.parse_expr_statement()
        elif token.type == 'SET_PROGRESS':
            self.advance()
            wid = self.parse_expression()
            self.expect('TO', suggestion="'to' after progress id")
            value = self.parse_expression()
            return SetProgressStmt(wid, value)
        elif token.type == 'EVERY':
            return self.parse_timer(repeating=True)
        elif token.type == 'AFTER':
            return self.parse_timer(repeating=False)
        elif token.type == 'BEEP':
            self.advance()
            freq = None; dur = None
            if self.peek() and self.peek().type == 'NUMBER':
                freq = Number(self.advance().value)
            if self.peek() and self.peek().type == 'NUMBER':
                dur = Number(self.advance().value)
            return BeepStmt(freq, dur)
        else:
            return self.parse_expr_statement()

    # ── GUI Parsers ──────────────────────────────────────────────────────────────

    def _at_end_of_line(self):
        t = self.peek().type if self.peek() else 'EOF'
        return t in ('NEWLINE', 'EOF', 'DEDENT')

    def _looks_like_widget(self):
        """canvas/slider/progress take a string id first; otherwise the word
        is being used as an ordinary identifier."""
        nxt = self.peek(1)
        return nxt is not None and nxt.type in ({'STRING', 'IDENT'} | SOFT_KEYWORD_TYPES)

    def _opt_keyword_val(self, keyword_type):
        """If next token is keyword_type, consume it and return next expression."""
        if self.peek() and self.peek().type == keyword_type:
            self.advance()
            return self.parse_expression()
        return None

    def _parse_widget_id(self):
        if self.peek() and self.peek().type == 'ID':
            self.advance()
            tok = self.peek()
            if tok and tok.type in ('STRING', 'NUMBER'):
                return String(str(self.advance().value))
            return self.parse_expression()
        return None

    def parse_window(self):
        self.advance()  # consume WINDOW
        title = self.parse_expression()
        width = 400
        height = 300
        color = None
        resizable = True
        widget_id = None
        while not self._at_end_of_line():
            t = self.peek().type
            if t == 'WIDTH':
                self.advance(); width = self.parse_expression()
            elif t == 'HEIGHT':
                self.advance(); height = self.parse_expression()
            elif t == 'COLOR':
                self.advance(); color = self.parse_expression()
            elif t == 'RESIZABLE':
                self.advance()
                resizable = self.parse_expression()
            elif t == 'ID':
                self.advance(); widget_id = self.parse_expression()
            else:
                break
        return WindowStmt(title, width, height, color, resizable, widget_id)

    def parse_label(self):
        self.advance()  # consume LABEL
        text = self.parse_expression()
        self.expect('AT', suggestion="'at X Y' after label text")
        x = self.parse_expression()
        y = self.parse_expression()
        font_size = None; color = None; widget_id = None
        while not self._at_end_of_line():
            t = self.peek().type
            if t == 'FONT_SIZE':
                self.advance(); font_size = self.parse_expression()
            elif t == 'COLOR':
                self.advance(); color = self.parse_expression()
            elif t == 'ID':
                self.advance(); widget_id = self.parse_expression()
            else:
                break
        return LabelStmt(text, x, y, font_size, color, widget_id)

    def parse_button(self):
        self.advance()  # consume BUTTON
        text = self.parse_expression()
        self.expect('AT', suggestion="'at X Y' after button text")
        x = self.parse_expression()
        y = self.parse_expression()
        width = None; height = None; on_click = None; color = None; widget_id = None
        while not self._at_end_of_line():
            t = self.peek().type
            if t == 'WIDTH':
                self.advance(); width = self.parse_expression()
            elif t == 'HEIGHT':
                self.advance(); height = self.parse_expression()
            elif t == 'ON_CLICK':
                self.advance()
                on_click = self.parse_name("function name after on_click")
            elif t == 'COLOR':
                self.advance(); color = self.parse_expression()
            elif t == 'ID':
                self.advance(); widget_id = self.parse_expression()
            else:
                break
        return ButtonStmt(text, x, y, width, height, on_click, color, widget_id)

    def parse_input_widget(self):
        self.advance()  # consume INPUT
        widget_id = self.parse_primary()  # usually a string literal id
        if isinstance(widget_id, Identifier):
            widget_id = String(widget_id.name)
        self.expect('AT', suggestion="'at X Y' after input id")
        x = self.parse_expression()
        y = self.parse_expression()
        width = None; placeholder = None; password = False
        while not self._at_end_of_line():
            t = self.peek().type
            if t == 'WIDTH':
                self.advance(); width = self.parse_expression()
            elif t == 'PLACEHOLDER':
                self.advance(); placeholder = self.parse_expression()
            elif t == 'PASSWORD':
                self.advance(); password = True
            else:
                break
        return InputStmt(widget_id, x, y, width, placeholder, password)

    def parse_image(self):
        self.advance()
        path = self.parse_expression()
        self.expect('AT', suggestion="'at X Y' after image path")
        x = self.parse_expression()
        y = self.parse_expression()
        width = None; height = None
        while not self._at_end_of_line():
            t = self.peek().type
            if t == 'WIDTH':
                self.advance(); width = self.parse_expression()
            elif t == 'HEIGHT':
                self.advance(); height = self.parse_expression()
            else:
                break
        return ImageStmt(path, x, y, width, height)

    def parse_textbox(self):
        self.advance()
        widget_id = self.parse_primary()
        if isinstance(widget_id, Identifier):
            widget_id = String(widget_id.name)
        self.expect('AT', suggestion="'at X Y' after textbox id")
        x = self.parse_expression()
        y = self.parse_expression()
        width = 200; height = 100
        while not self._at_end_of_line():
            t = self.peek().type
            if t == 'WIDTH':
                self.advance(); width = self.parse_expression()
            elif t == 'HEIGHT':
                self.advance(); height = self.parse_expression()
            else:
                break
        return TextboxStmt(widget_id, x, y, width, height)

    def parse_checkbox(self):
        self.advance()
        widget_id = self.parse_primary()
        if isinstance(widget_id, Identifier):
            widget_id = String(widget_id.name)
        text = None; on_change = None
        while not self._at_end_of_line() and self.peek().type != 'AT':
            t = self.peek().type
            if t == 'TEXT':
                self.advance(); text = self.parse_expression()
            elif t == 'ON_CHANGE':
                self.advance(); on_change = self.parse_name("function name after on_change")
            else:
                break
        self.expect('AT', suggestion="'at X Y' after checkbox")
        x = self.parse_expression()
        y = self.parse_expression()
        return CheckboxStmt(widget_id, text, x, y, on_change)

    def parse_dropdown(self):
        self.advance()
        widget_id = self.parse_primary()
        if isinstance(widget_id, Identifier):
            widget_id = String(widget_id.name)
        self.expect('OPTIONS', suggestion="'options [...]' after dropdown id")
        options = self.parse_primary()  # list literal
        self.expect('AT', suggestion="'at X Y' after dropdown options")
        x = self.parse_expression()
        y = self.parse_expression()
        on_change = None
        if self.peek() and self.peek().type == 'ON_CHANGE':
            self.advance(); on_change = self.parse_name("function name after on_change")
        return DropdownStmt(widget_id, options, x, y, on_change)

    def parse_set_text(self):
        self.advance()
        widget_id = self.parse_expression()
        self.expect('TO', suggestion="'to' after widget id")
        value = self.parse_expression()
        return SetTextStmt(widget_id, value)

    def parse_show_window(self):
        self.advance()
        return ShowWindowStmt()

    def parse_alert(self):
        self.advance()
        message = self.parse_expression()
        return AlertStmt(message)

    def parse_set_color(self):
        self.advance()
        widget_id = self.parse_expression()
        self.expect('TO', suggestion="'to' after widget id")
        color = self.parse_expression()
        return SetColorStmt(widget_id, color)

    def parse_set_visible(self):
        self.advance()
        widget_id = self.parse_expression()
        visible = self.parse_expression()
        return SetVisibleStmt(widget_id, visible)

    # ── Creative / Canvas Parsers ────────────────────────────────────────────────

    def parse_canvas_widget(self):
        self.advance()
        widget_id = self.parse_primary()
        if isinstance(widget_id, Identifier):
            widget_id = String(widget_id.name)
        width = 300; height = 300; color = None
        while not self._at_end_of_line():
            t = self.peek().type
            if t == 'WIDTH':
                self.advance(); width = self.parse_expression()
            elif t == 'HEIGHT':
                self.advance(); height = self.parse_expression()
            elif t == 'COLOR':
                self.advance(); color = self.parse_expression()
            else:
                break
        return CanvasStmt(widget_id, width, height, color)

    def _parse_draw_options(self):
        color = None; fill = None; outline_width = None; text = None
        while not self._at_end_of_line():
            t = self.peek().type
            if t == 'COLOR':
                self.advance(); color = self.parse_expression()
            elif t == 'FILL':
                self.advance(); fill = self.parse_expression()
            elif t == 'WIDTH':
                self.advance(); outline_width = self.parse_expression()
            elif t == 'TEXT':
                self.advance(); text = self.parse_expression()
            else:
                break
        return color, fill, outline_width, text

    def parse_draw(self):
        self.advance()  # DRAW
        shape_tok = self.peek()
        shape = self.parse_name("shape to draw (line, rectangle, circle, oval, dot, text)")
        self.expect('ON', suggestion="e.g. draw line on \"cv\" from 0 0 to 100 100")
        canvas_id = self.parse_expression()

        coords = []
        text = None
        if shape in ('line', 'rectangle', 'rect', 'box'):
            self.expect('FROM', suggestion=f"'from X1 Y1 to X2 Y2' after draw {shape}")
            coords.append(self.parse_expression())
            coords.append(self.parse_expression())
            self.expect('TO', suggestion="'to X2 Y2'")
            coords.append(self.parse_expression())
            coords.append(self.parse_expression())
        elif shape in ('circle', 'oval', 'dot'):
            self.expect('AT', suggestion=f"'at CX CY size R' after draw {shape}")
            coords.append(self.parse_expression())
            coords.append(self.parse_expression())
            tok = self.peek()
            if tok and tok.type == 'SIZE':
                self.advance()
                coords.append(self.parse_expression())
            else:
                coords.append(Number(10))  # default radius
        elif shape == 'text':
            self.expect('AT', suggestion="'at X Y' after draw text")
            coords.append(self.parse_expression())
            coords.append(self.parse_expression())
        else:
            raise ParserError(
                f"I don't know how to draw '{shape}'",
                line=shape_tok.line if shape_tok else None,
                column=shape_tok.column if shape_tok else None,
                suggestion="Try line, rectangle, circle, oval, dot or text"
            )

        color, fill, outline_width, text = self._parse_draw_options()
        if shape in ('rect', 'box'):
            shape = 'rectangle'
        if shape == 'oval' and len(coords) >= 3:
            shape = 'circle'
        return DrawStmt(shape, canvas_id, coords, color, fill, outline_width, text)

    def parse_slider_widget(self):
        self.advance()
        widget_id = self.parse_primary()
        if isinstance(widget_id, Identifier):
            widget_id = String(widget_id.name)
        minimum = Number(0); maximum = Number(100)
        while not self._at_end_of_line() and self.peek().type != 'AT':
            t = self.peek().type
            if t == 'FROM':
                self.advance(); minimum = self.parse_expression()
            elif t == 'TO':
                self.advance(); maximum = self.parse_expression()
            elif t == 'ON_CHANGE':
                break
            else:
                break
        self.expect('AT', suggestion="'at X Y' after slider")
        x = self.parse_expression()
        y = self.parse_expression()
        on_change = None
        if self.peek() and self.peek().type == 'ON_CHANGE':
            self.advance(); on_change = self.parse_name("function name after on_change")
        return SliderStmt(widget_id, minimum, maximum, x, y, on_change)

    def parse_progress_widget(self):
        self.advance()
        widget_id = self.parse_primary()
        if isinstance(widget_id, Identifier):
            widget_id = String(widget_id.name)
        self.expect('AT', suggestion="'at X Y' after progress id")
        x = self.parse_expression()
        y = self.parse_expression()
        width = None; value = None
        while not self._at_end_of_line():
            t = self.peek().type
            if t == 'WIDTH':
                self.advance(); width = self.parse_expression()
            else:
                break
        return ProgressStmt(widget_id, x, y, width)

    def parse_timer(self, repeating=True):
        self.advance()  # EVERY / AFTER
        amount = self.eval_number_token()
        unit_ms = True
        tok = self.peek()
        if tok and tok.type in ('SECONDS', 'SECOND'):
            self.advance()
            unit_ms = False
        elif tok and tok.type in ('MILLIS', 'MILLISECONDS', 'MS'):
            self.advance()
        call_tok = self.peek()
        if call_tok is None or call_tok.type != 'CALL':
            raise ParserError(
                "I expected 'call' here",
                line=call_tok.line if call_tok else None,
                column=call_tok.column if call_tok else None,
                suggestion="e.g. every 500 milliseconds call tick"
            )
        self.advance()
        handler = self.parse_name("function name after 'call'")
        if repeating:
            return TimerStmt(amount, handler, unit_ms)
        return AfterStmt(amount, handler, unit_ms)

    def eval_number_token(self):
        tok = self.peek()
        if tok is None or tok.type != 'NUMBER':
            raise ParserError(
                "I expected a number here",
                line=tok.line if tok else None,
                column=tok.column if tok else None,
                suggestion="e.g. every 1000 milliseconds call tick"
            )
        return Number(self.advance().value)

    def parse_say(self):
        self.advance()  # consume SAY
        expr = self.parse_expression()
        return SayStmt(expr)

    def parse_func_def(self):
        self.advance()
        name_token = self.parse_name("function name after 'func'", allow_soft=False)
        self.expect('LPAREN', suggestion="opening parenthesis '(' after function name")
        params = []
        if self.peek() and self.peek().type in ('IDENT',) or (self.peek() and self.peek().type in SOFT_KEYWORD_TYPES):
            params.append(self.parse_name("parameter name"))
            while self.peek() and self.peek().type == 'COMMA':
                self.advance()
                params.append(self.parse_name("parameter name"))
        self.expect('RPAREN', suggestion="closing parenthesis ')' after parameters")
        self.expect('COLON', suggestion="colon ':' after function declaration")
        body = self.parse_block()
        return FuncDef(name_token, params, body)

    def parse_class_def(self):
        self.advance()
        name_token = self.parse_name("class name after 'class'", allow_soft=False)
        self.expect('COLON', suggestion="colon ':' after class name")
        body = self.parse_class_body()
        return ClassDef(name_token, body)

    def parse_class_body(self):
        body = []
        if self.peek().type == 'INDENT':
            self.advance()
            while self.peek().type != 'DEDENT' and self.peek().type != 'EOF':
                if self.peek().type == 'NEWLINE':
                    self.advance()
                    continue
                if self.peek().type == 'FUNC':
                    body.append(self.parse_func_def())
                else:
                    raise ParserError(
                        f"Only functions are allowed inside a class",
                        line=self.peek().line,
                        column=self.peek().column
                    )
            if self.peek().type == 'DEDENT':
                self.advance()
        return body

    def parse_if(self):
        self.advance()
        condition = self.parse_expression()
        self.expect('COLON', suggestion="colon ':' after 'if' condition")
        consequent = self.parse_block()
        alternates = []
        while self.peek() and self.peek().type == 'ELIF':
            self.advance()
            alt_condition = self.parse_expression()
            self.expect('COLON', suggestion="colon ':' after 'elif' condition")
            alt_body = self.parse_block()
            alternates.append((alt_condition, alt_body))
        else_body = None
        if self.peek() and self.peek().type == 'ELSE':
            self.advance()
            self.expect('COLON', suggestion="colon ':' after 'else'")
            else_body = self.parse_block()
        return IfStmt(condition, consequent, alternates, else_body)

    def parse_for(self):
        self.advance()
        var_token = self.parse_name("loop variable after 'for'")
        self.expect('IN', suggestion="'in' after loop variable")
        iterable = self.parse_expression()
        self.expect('COLON', suggestion="colon ':' after 'for' loop header")
        body = self.parse_block()
        return ForStmt(var_token, iterable, body)

    def parse_while(self):
        self.advance()
        condition = self.parse_expression()
        self.expect('COLON', suggestion="colon ':' after 'while' condition")
        body = self.parse_block()
        return WhileStmt(condition, body)

    def parse_repeat(self):
        self.advance()
        count = self.parse_expression()
        times_tok = self.peek()
        if times_tok is None or times_tok.type != 'TIMES':
            raise ParserError(
                "I expected 'times' here",
                line=times_tok.line if times_tok else None,
                column=times_tok.column if times_tok else None,
                suggestion="e.g. repeat 5 times:"
            )
        self.advance()
        self.expect('COLON', suggestion="colon ':' after 'repeat N times'")
        body = self.parse_block()
        return RepeatStmt(count, body)

    def parse_switch(self):
        self.advance()
        subject = self.parse_expression()
        self.expect('COLON', suggestion="colon ':' after 'switch' value")
        tok = self.peek()
        if not tok or tok.type != 'INDENT':
            raise ParserError(
                "I expected an indented 'case' after 'switch'",
                line=tok.line if tok else None,
                column=tok.column if tok.column else None if tok else None,
                suggestion="Indent the cases under switch"
            )
        self.advance()  # INDENT
        cases = []
        default_body = None
        while self.peek() and self.peek().type in ('CASE', 'DEFAULT'):
            if self.peek().type == 'CASE':
                self.advance()
                case_values = [self.parse_expression()]
                while self.peek() and self.peek().type == 'COMMA':
                    self.advance()
                    case_values.append(self.parse_expression())
                self.expect('COLON', suggestion="colon ':' after case value")
                body = self.parse_block()
                cases.append((case_values, body))
            else:
                self.advance()
                self.expect('COLON', suggestion="colon ':' after 'default'")
                default_body = self.parse_block()
        if self.peek() and self.peek().type == 'DEDENT':
            self.advance()
        else:
            bad = self.peek()
            raise ParserError(
                "Only 'case' and 'default' are allowed directly inside a switch",
                line=bad.line if bad else None,
                column=bad.column if bad else None
            )
        if not cases and default_body is None:
            raise ParserError(
                "A switch needs at least one 'case'",
                suggestion="e.g. switch x: / case 1: ... / default:"
            )
        return SwitchStmt(subject, cases, default_body)

    def parse_try_catch(self):
        self.advance()
        self.expect('COLON', suggestion="colon ':' after 'try'")
        try_body = self.parse_block()
        catch_var = None
        catch_body = None
        if self.peek() and self.peek().type == 'CATCH':
            self.advance()
            # catch e:  or just catch:
            if self.peek() and (self.peek().type == 'IDENT' or self.peek().type in SOFT_KEYWORD_TYPES):
                catch_var = self.parse_name("variable name after 'catch'")
            self.expect('COLON', suggestion="colon ':' after 'catch'")
            catch_body = self.parse_block()
        return TryCatch(try_body, catch_var, catch_body)

    def parse_return(self):
        self.advance()
        value = None
        if self.peek().type not in ('NEWLINE', 'EOF', 'DEDENT'):
            value = self.parse_expression()
        return ReturnStmt(value)

    def parse_import(self):
        self.advance()
        path_token = self.expect('STRING', suggestion="file path in quotes after 'import'")
        return ImportStmt(path_token.value)

    def parse_block(self):
        statements = []
        if self.peek().type == 'INDENT':
            self.advance()
            while self.peek().type != 'DEDENT' and self.peek().type != 'EOF':
                if self.peek().type == 'NEWLINE':
                    self.advance()
                    continue
                stmt = self.parse_statement()
                statements.append(stmt)
            if self.peek().type == 'DEDENT':
                self.advance()
        else:
            if self.peek().type == 'NEWLINE':
                self.advance()
                return statements
            stmt = self.parse_statement()
            statements.append(stmt)
        return statements

    def parse_expr_statement(self):
        # Return the expression itself (assignments/calls evaluate fine standalone)
        return self.parse_expression()

    def parse_expression(self):
        return self.parse_assignment()

    ASSIGN_OPS = {
        'ASSIGN': None,
        'PLUS_ASSIGN': '+',
        'MINUS_ASSIGN': '-',
        'MULT_ASSIGN': '*',
        'DIV_ASSIGN': '/',
        'MOD_ASSIGN': '%',
    }

    def parse_assignment(self):
        left = self.parse_or()
        tok = self.peek()
        if tok and tok.type in self.ASSIGN_OPS:
            op = self.ASSIGN_OPS[tok.type]
            self.advance()
            value = self.parse_expression()
            if op is not None:
                # sugar: x += v  →  x = x + v
                from copy import copy
                if isinstance(left, Identifier):
                    left_val = Identifier(left.name)
                elif isinstance(left, IndexAccess):
                    left_val = IndexAccess(left.obj, left.index)
                elif isinstance(left, MemberAccess):
                    left_val = MemberAccess(left.obj, left.member)
                else:
                    raise ParserError(
                        "Invalid assignment target",
                        line=tok.line, column=tok.column,
                        suggestion="Assign to a variable, list item, or property"
                    )
                value = BinaryOp(left_val, op, value)
            if isinstance(left, Identifier):
                return Assignment(left.name, value)
            elif isinstance(left, MemberAccess):
                return PropertyAssignment(left.obj, left.member, value)
            elif isinstance(left, IndexAccess):
                return IndexAssignment(left.obj, left.index, value)
            raise ParserError(
                "Invalid assignment target",
                line=tok.line, column=tok.column,
                suggestion="Assign to a variable, list item, or property"
            )
        return left

    def parse_comparison(self):
        left = self.parse_term()
        comp_ops = ['IS_GREATER_THAN', 'IS_LESS_THAN', 'IS_EQUAL_TO',
                    'IS_GREATER_EQUAL', 'IS_LESS_EQUAL', 'IS_NOT', 'IS']
        while True:
            tok = self.peek()
            if tok and tok.type in comp_ops:
                op = self.advance().value
                right = self.parse_term()
                left = self._mark(Comparison(left, op, right), tok)
            elif tok and tok.type == 'IN':
                self.advance()
                right = self.parse_term()
                left = self._mark(Comparison(left, 'in', right), tok)
            elif tok and tok.type == 'NOT' and self.peek(1) \
                    and self.peek(1).type == 'IN':
                op_tok = self.advance()  # not
                self.advance()           # in
                right = self.parse_term()
                left = self._mark(Comparison(left, 'not in', right), op_tok)
            else:
                break
        return left

    # Correct precedence: or < and < comparison < term < factor < unary
    def parse_or(self):
        left = self.parse_and()
        while self.peek() and self.peek().type == 'OR':
            tok = self.advance()
            right = self.parse_and()
            left = self._mark(LogicalOp(left, tok.value, right), tok)
        return left

    def parse_and(self):
        left = self.parse_comparison()
        while self.peek() and self.peek().type == 'AND':
            tok = self.advance()
            right = self.parse_comparison()
            left = self._mark(LogicalOp(left, tok.value, right), tok)
        return left

    def parse_term(self):
        left = self.parse_factor()
        while self.peek() and self.peek().type in ('PLUS', 'MINUS'):
            tok = self.advance()
            right = self.parse_factor()
            left = self._mark(BinaryOp(left, tok.value, right), tok)
        return left

    def parse_factor(self):
        left = self.parse_unary()
        while self.peek() and self.peek().type in ('MULT', 'DIV', 'MOD', 'POW'):
            tok = self.advance()
            right = self.parse_unary()
            left = self._mark(BinaryOp(left, tok.value, right), tok)
        return left

    def parse_unary(self):
        tok = self.peek()
        if tok and tok.type == 'NOT':
            self.advance()
            operand = self.parse_unary()
            return UnaryOp('not', operand)
        if tok and tok.type == 'MINUS':
            self.advance()
            operand = self.parse_unary()
            return UnaryOp('-', operand)
        return self.parse_postfix()

    def parse_postfix(self):
        start = self.peek()
        expr = self.parse_primary()
        while True:
            tok = self.peek()
            if tok is None:
                break
            if tok.type == 'LBRACKET':
                self.advance()
                index = self.parse_expression()
                self.expect('RBRACKET', suggestion="closing bracket ']' after index")
                expr = IndexAccess(expr, index)
            elif tok.type == 'DOT':
                self.advance()
                member_token = self.peek()
                if member_token is None or member_token.type not in ({'IDENT'} | SOFT_KEYWORD_TYPES):
                    raise ParserError(
                        "I expected a member name after '.'",
                        line=member_token.line if member_token else None,
                        column=member_token.column if member_token else None
                    )
                member = self.advance().value.lower()
                if self.peek() and self.peek().type == 'LPAREN':
                    args = self.parse_args()
                    expr = MethodCall(expr, member, args)
                else:
                    expr = MemberAccess(expr, member)
            elif tok.type == 'STRING' and isinstance(expr, Identifier):
                # Function-call shorthand: read_file "notes.txt", true
                nxt = self.peek(1)
                if nxt is None or nxt.type in ('NEWLINE', 'EOF', 'DEDENT', 'COMMA'):
                    self.advance()
                    args = [String(tok.value)]
                    while self.peek() and self.peek().type == 'COMMA':
                        self.advance()
                        args.append(self.parse_expression())
                    expr = FuncCall(expr.name, args)
                    continue
                break
            else:
                break
        return self._mark(expr, start)

    def parse_input_call(self):
        """input("prompt") used as an expression."""
        self.advance()  # consume INPUT
        args = []
        if self.peek() and self.peek().type == 'LPAREN':
            args = self.parse_args()
        else:
            tok = self.peek()
            if tok and tok.type == 'STRING':
                args = [String(self.advance().value)]
        return FuncCall('input', args)

    def parse_primary(self):
        start = self.peek()
        expr = self._primary_impl()
        return self._mark(expr, start)

    def _primary_impl(self):
        token = self.peek()
        if token is None:
            raise ParserError("Unexpected end of file")

        if token.type == 'NUMBER':
            self.advance()
            return Number(token.value)

        if token.type == 'STRING':
            self.advance()
            return String(token.value)

        if token.type == 'TRUE':
            self.advance()
            return Boolean(True)

        if token.type == 'FALSE':
            self.advance()
            return Boolean(False)

        if token.type == 'NULL':
            self.advance()
            return Null()

        if token.type == 'INPUT':
            return self.parse_input_call()

        if token.type == 'GET_TEXT':
            self.advance()
            widget_id = self.parse_primary()
            return GetTextExpr(widget_id)

        if token.type == 'IDENT' or token.type in SOFT_KEYWORD_TYPES or \
                token.type in ('WINDOW', 'LABEL', 'BUTTON', 'IMAGE', 'TEXTBOX',
                               'CHECKBOX', 'DROPDOWN', 'ALERT',
                               'SET_TEXT', 'SET_COLOR', 'SET_VISIBLE', 'SHOW_WINDOW'):
            self.advance()
            name = str(token.value).lower() if token.type != 'IDENT' else token.value
            if name == 'self':
                return Identifier('self')
            if self.peek() and self.peek().type == 'LPAREN':
                args = self.parse_args()
                return FuncCall(name, args)
            return Identifier(name)

        if token.type == 'SELF':
            self.advance()
            return Identifier('self')

        if token.type == 'LPAREN':
            self.advance()
            expr = self.parse_expression()
            self.expect('RPAREN', suggestion="closing parenthesis ')'")
            return expr

        if token.type == 'LBRACKET':
            return self.parse_list_literal()

        if token.type == 'LBRACE':
            return self.parse_dict_literal()

        raise ParserError(
            f"I expected a value here but found {self._describe(token)}",
            line=token.line, column=token.column
        )

    def parse_args(self):
        self.advance()  # LPAREN
        args = []
        if self.peek().type != 'RPAREN':
            args.append(self.parse_expression())
            while self.peek() and self.peek().type == 'COMMA':
                self.advance()
                args.append(self.parse_expression())
        self.expect('RPAREN', suggestion="closing parenthesis ')' after arguments")
        return args

    def parse_list_literal(self):
        self.advance()
        elements = []
        if self.peek().type != 'RBRACKET':
            elements.append(self.parse_expression())
            while self.peek() and self.peek().type == 'COMMA':
                self.advance()
                elements.append(self.parse_expression())
        self.expect('RBRACKET', suggestion="closing bracket ']' after list elements")
        return ListLiteral(elements)

    def parse_dict_literal(self):
        self.advance()
        pairs = []
        if self.peek().type != 'RBRACE':
            key = self.parse_expression()
            self.expect('COLON', suggestion="colon ':' after dictionary key")
            value = self.parse_expression()
            pairs.append((key, value))
            while self.peek() and self.peek().type == 'COMMA':
                self.advance()
                key = self.parse_expression()
                self.expect('COLON', suggestion="colon ':' after dictionary key")
                value = self.parse_expression()
                pairs.append((key, value))
        self.expect('RBRACE', suggestion="closing brace '}' after dictionary")
        return DictLiteral(pairs)
