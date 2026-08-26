class EppError(Exception):
    def __init__(self, message, line=None, column=None, suggestion=None):
        self.line = line
        self.column = column
        self.suggestion = suggestion
        super().__init__(message)

    def __str__(self):
        msg = super().__str__()
        if self.line is not None:
            if self.column is not None:
                msg = f"Error at line {self.line}, column {self.column}: {msg}"
            else:
                msg = f"Error at line {self.line}: {msg}"
        if self.suggestion:
            msg += f" — {self.suggestion}"
        return msg

class LexerError(EppError):
    pass

class ParserError(EppError):
    pass

class EvalError(EppError):
    pass

class ReturnException(Exception):
    def __init__(self, value):
        self.value = value
        super().__init__(str(value))

class BreakException(Exception):
    pass

class ContinueException(Exception):
    pass