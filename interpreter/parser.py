from interpreter.nodes import *
from interpreter.errors import ParserError

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

    def expect(self, token_type, suggestion=None):
        token = self.peek()
        if token is None or token.type != token_type:
            expected = token_type
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
            stmt = self.parse_statement()
            statements.append(stmt)
        return Program(statements)

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
            return self.parse_input_widget()
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
        elif token.type == 'GET_TEXT':
            return self.parse_get_text()
        elif token.type == 'SHOW_WINDOW':
            return self.parse_show_window()
        elif token.type == 'ALERT':
            return self.parse_alert()
        elif token.type == 'SET_COLOR':
            return self.parse_set_color()
        elif token.type == 'SET_VISIBLE':
            return self.parse_set_visible()
        else:
            return self.parse_expr_statement()

    # ── GUI Parsers ──────────────────────────────────────────────────────────────

    def _opt(self, token_type):
        """Consume token if it matches, return value or None."""
        if self.peek() and self.peek().type == token_type:
            return self.advance().value
        return None

    def _opt_keyword_val(self, keyword_type):
        """If next token is keyword_type, consume it and return next expression."""
        if self.peek() and self.peek().type == keyword_type:
            self.advance()
            return self.parse_expression()
        return None

    def parse_window(self):
        self.advance()  # consume WINDOW
        title  = self.parse_expression()
        width  = 400
        height = 300
        color  = None
        resizable = True
        while self.peek() and self.peek().type not in ('NEWLINE', 'EOF', 'DEDENT'):
            t = self.peek().type
            if t == 'WIDTH':
                self.advance(); width = self.parse_expression()
            elif t == 'HEIGHT':
                self.advance(); height = self.parse_expression()
            elif t == 'COLOR':
                self.advance(); color = self.parse_expression()
            elif t == 'RESIZABLE':
                self.advance()
                v = self.parse_expression()
                resizable = v
            else:
                break
        return WindowStmt(title, width, height, color, resizable)

    def parse_label(self):
        self.advance()  # consume LABEL
        text = self.parse_expression()
        self.expect('AT', suggestion="'at' after label text")
        x = self.parse_expression()
        y = self.parse_expression()
        font_size = None; color = None; widget_id = None
        while self.peek() and self.peek().type not in ('NEWLINE', 'EOF', 'DEDENT'):
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
        self.expect('AT', suggestion="'at' after button text")
        x = self.parse_expression()
        y = self.parse_expression()
        width = None; height = None; on_click = None; color = None; widget_id = None
        while self.peek() and self.peek().type not in ('NEWLINE', 'EOF', 'DEDENT'):
            t = self.peek().type
            if t == 'WIDTH':
                self.advance(); width = self.parse_expression()
            elif t == 'HEIGHT':
                self.advance(); height = self.parse_expression()
            elif t == 'ON_CLICK':
                self.advance()
                on_click = self.peek().value
                self.advance()
            elif t == 'COLOR':
                self.advance(); color = self.parse_expression()
            elif t == 'ID':
                self.advance(); widget_id = self.parse_expression()
            else:
                break
        return ButtonStmt(text, x, y, width, height, on_click, color, widget_id)

    def parse_input_widget(self):
        self.advance()  # consume INPUT
        widget_id = self.parse_expression()
        self.expect('AT', suggestion="'at' after input id")
        x = self.parse_expression()
        y = self.parse_expression()
        width = None; placeholder = None; password = False
        while self.peek() and self.peek().type not in ('NEWLINE', 'EOF', 'DEDENT'):
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
        self.expect('AT', suggestion="'at' after image path")
        x = self.parse_expression()
        y = self.parse_expression()
        width = None; height = None
        while self.peek() and self.peek().type not in ('NEWLINE', 'EOF', 'DEDENT'):
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
        widget_id = self.parse_expression()
        self.expect('AT', suggestion="'at' after textbox id")
        x = self.parse_expression()
        y = self.parse_expression()
        width = 200; height = 100
        while self.peek() and self.peek().type not in ('NEWLINE', 'EOF', 'DEDENT'):
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
        widget_id = self.parse_expression()
        text = None; on_change = None
        while self.peek() and self.peek().type not in ('NEWLINE', 'EOF', 'DEDENT', 'AT'):
            t = self.peek().type
            if t == 'TEXT':
                self.advance(); text = self.parse_expression()
            elif t == 'ON_CHANGE':
                self.advance(); on_change = self.peek().value; self.advance()
            else:
                break
        self.expect('AT', suggestion="'at X Y' after checkbox")
        x = self.parse_expression()
        y = self.parse_expression()
        return CheckboxStmt(widget_id, text, x, y, on_change)

    def parse_dropdown(self):
        self.advance()
        widget_id = self.parse_expression()
        self.expect('OPTIONS', suggestion="'options [...]' after dropdown id")
        options = self.parse_primary()  # parse list literal
        self.expect('AT', suggestion="'at X Y' after dropdown options")
        x = self.parse_expression()
        y = self.parse_expression()
        on_change = None
        if self.peek() and self.peek().type == 'ON_CHANGE':
            self.advance(); on_change = self.peek().value; self.advance()
        return DropdownStmt(widget_id, options, x, y, on_change)

    def parse_set_text(self):
        self.advance()
        widget_id = self.parse_expression()
        self.expect('TO', suggestion="'to' after widget id")
        value = self.parse_expression()
        return SetTextStmt(widget_id, value)

    def parse_get_text(self):
        self.advance()
        widget_id = self.parse_expression()
        return GetTextStmt(widget_id)

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

    def parse_say(self):
        self.advance()  # consume SAY
        expr = self.parse_expression()
        return SayStmt(expr)

    def parse_func_def(self):
        self.advance()
        name_token = self.expect('IDENT', suggestion="function name after 'func'")
        self.expect('LPAREN', suggestion="opening parenthesis '(' after function name")
        params = []
        if self.peek().type == 'IDENT':
            params.append(self.advance().value)
            while self.peek().type == 'COMMA':
                self.advance()
                param = self.expect('IDENT', suggestion="parameter name")
                params.append(param.value)
        self.expect('RPAREN', suggestion="closing parenthesis ')' after parameters")
        self.expect('COLON', suggestion="colon ':' after function declaration")
        body = self.parse_block()
        return FuncDef(name_token.value, params, body)

    def parse_class_def(self):
        self.advance()
        name_token = self.expect('IDENT', suggestion="class name after 'class'")
        self.expect('COLON', suggestion="colon ':' after class name")
        body = self.parse_class_body()
        return ClassDef(name_token.value, body)

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
        var_token = self.expect('IDENT', suggestion="loop variable after 'for'")
        self.expect('IN', suggestion="'in' after loop variable")
        iterable = self.parse_expression()
        self.expect('COLON', suggestion="colon ':' after 'for' loop header")
        body = self.parse_block()
        return ForStmt(var_token.value, iterable, body)

    def parse_while(self):
        self.advance()
        condition = self.parse_expression()
        self.expect('COLON', suggestion="colon ':' after 'while' condition")
        body = self.parse_block()
        return WhileStmt(condition, body)

    def parse_try_catch(self):
        self.advance()
        self.expect('COLON', suggestion="colon ':' after 'try'")
        try_body = self.parse_block()
        catch_var = None
        catch_body = None
        if self.peek() and self.peek().type == 'CATCH':
            self.advance()
            var_token = self.expect('IDENT', suggestion="variable name after 'catch'")
            self.expect('COLON', suggestion="colon ':' after 'catch' variable")
            catch_body = self.parse_block()
            catch_var = var_token.value
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
        expr = self.parse_expression()
        return ExpressionStatement(expr)

    def parse_expression(self):
        return self.parse_assignment()

    def parse_assignment(self):
        left = self.parse_comparison()
        if self.peek() and self.peek().type == 'ASSIGN':
            self.advance()
            value = self.parse_expression()
            if isinstance(left, Identifier):
                return Assignment(left.name, value)
            elif isinstance(left, MemberAccess):
                return PropertyAssignment(left.obj, left.member, value)
            elif isinstance(left, IndexAccess):
                return IndexAssignment(left.obj, left.index, value)
        return left

    def parse_comparison(self):
        left = self.parse_logical()
        comp_ops = ['IS_GREATER_THAN', 'IS_LESS_THAN', 'IS_EQUAL_TO',
                    'IS_GREATER_EQUAL', 'IS_LESS_EQUAL', 'IS_NOT', 'IS']
        while self.peek() and self.peek().type in comp_ops:
            op = self.advance().value
            right = self.parse_logical()
            left = Comparison(left, op, right)
        return left

    def parse_logical(self):
        left = self.parse_term()
        while self.peek() and self.peek().type in ('AND', 'OR'):
            op = self.advance().value
            right = self.parse_term()
            left = LogicalOp(left, op, right)
        return left

    def parse_term(self):
        left = self.parse_factor()
        while self.peek() and self.peek().type in ('PLUS', 'MINUS'):
            op = self.advance().value
            right = self.parse_factor()
            left = BinaryOp(left, op, right)
        return left

    def parse_factor(self):
        left = self.parse_unary()
        while self.peek() and self.peek().type in ('MULT', 'DIV'):
            op = self.advance().value
            right = self.parse_unary()
            left = BinaryOp(left, op, right)
        return left

    def parse_unary(self):
        if self.peek() and self.peek().type == 'NOT':
            self.advance()
            operand = self.parse_unary()
            return UnaryOp('not', operand)
        return self.parse_primary()

    def parse_primary(self):
        token = self.peek()

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

        if token.type == 'IDENT':
            self.advance()
            name = token.value
            if self.peek() and self.peek().type == 'LPAREN':
                args = self.parse_args()
                return FuncCall(name, args)
            elif self.peek() and self.peek().type == 'DOT':
                return self.parse_member_access(Identifier(name))
            return Identifier(name)
        
        if token.type == 'SELF':
            self.advance()
            if self.peek() and self.peek().type == 'DOT':
                return self.parse_member_access(Identifier('self'))
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

        # get_text used as expression: x = get_text "box"
        if token.type == 'GET_TEXT':
            self.advance()
            widget_id = self.parse_primary()
            return GetTextStmt(widget_id)

        raise ParserError(
            f"I expected a value here — did you forget something?",
            line=token.line if token else None,
            column=token.column if token else None
        )

    def parse_args(self):
        self.advance()
        args = []
        if self.peek().type != 'RPAREN':
            args.append(self.parse_expression())
            while self.peek() and self.peek().type == 'COMMA':
                self.advance()
                args.append(self.parse_expression())
        self.expect('RPAREN', suggestion="closing parenthesis ')' after arguments")
        return args

    def parse_member_access(self, obj):
        while self.peek() and self.peek().type == 'DOT':
            self.advance()  # consume DOT
            member_token = self.expect('IDENT', suggestion="member name after '.'")
            member = member_token.value
            if self.peek() and self.peek().type == 'LPAREN':
                args = self.parse_args()
                obj = MethodCall(obj, member, args)
            else:
                obj = MemberAccess(obj, member)
        return obj

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