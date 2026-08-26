class Node:
    pass

class Program(Node):
    def __init__(self, statements):
        self.statements = statements

class Number(Node):
    def __init__(self, value):
        self.value = value

class String(Node):
    def __init__(self, value):
        self.value = value

class Boolean(Node):
    def __init__(self, value):
        self.value = value

class Null(Node):
    instance = None

class Identifier(Node):
    def __init__(self, name):
        self.name = name

class ListLiteral(Node):
    def __init__(self, elements):
        self.elements = elements

class DictLiteral(Node):
    def __init__(self, pairs):
        self.pairs = pairs

class BinaryOp(Node):
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right

class UnaryOp(Node):
    def __init__(self, operator, operand):
        self.operator = operator
        self.operand = operand

class Comparison(Node):
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right

class LogicalOp(Node):
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right

class Assignment(Node):
    def __init__(self, name, value):
        self.name = name
        self.value = value

class FuncCall(Node):
    def __init__(self, name, args):
        self.name = name
        self.args = args

class MethodCall(Node):
    def __init__(self, obj, method, args):
        self.obj = obj
        self.method = method
        self.args = args

class IndexAccess(Node):
    def __init__(self, obj, index):
        self.obj = obj
        self.index = index

class FuncDef(Node):
    def __init__(self, name, params, body):
        self.name = name
        self.params = params
        self.body = body

class ClassDef(Node):
    def __init__(self, name, body):
        self.name = name
        self.body = body

class IfStmt(Node):
    def __init__(self, condition, consequent, alternates, else_body=None):
        self.condition = condition
        self.consequent = consequent
        self.alternates = alternates
        self.else_body = else_body

class ForStmt(Node):
    def __init__(self, variable, iterable, body):
        self.variable = variable
        self.iterable = iterable
        self.body = body

class WhileStmt(Node):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

class TryCatch(Node):
    def __init__(self, try_body, catch_var=None, catch_body=None):
        self.try_body = try_body
        self.catch_var = catch_var
        self.catch_body = catch_body

class RepeatStmt(Node):
    """repeat <count> times:"""
    def __init__(self, count, body):
        self.count = count
        self.body = body

class SwitchStmt(Node):
    """switch <expr>: / case v[, v2]: ... / default:"""
    def __init__(self, subject, cases, default_body=None):
        self.subject = subject
        self.cases = cases          # list of ([values], body)
        self.default_body = default_body

class BreakStmt(Node):
    pass

class ContinueStmt(Node):
    pass

class TestStmt(Node):
    """test "name": ...body... — groups expectations into a named test"""
    def __init__(self, name, body):
        self.name = name
        self.body = body

class ExpectStmt(Node):
    """expect <expr> to_be <expr> | to_be_true | to_be_false | to_throw"""
    def __init__(self, expr, matcher, expected=None):
        self.expr = expr
        self.matcher = matcher    # 'to_be' | 'to_be_true' | 'to_be_false' | 'to_throw'
        self.expected = expected

class BreakException(Exception):
    pass

class ContinueException(Exception):
    pass

class ReturnStmt(Node):
    def __init__(self, value):
        self.value = value

class ImportStmt(Node):
    def __init__(self, path):
        self.path = path

class ExpressionStatement(Node):
    def __init__(self, expr):
        self.expr = expr

class MemberAccess(Node):
    def __init__(self, obj, member):
        self.obj = obj
        self.member = member

class SayStmt(Node):
    def __init__(self, expr):
        self.expr = expr

class Call(Node):
    def __init__(self, func, args):
        self.func = func
        self.args = args

class PropertyAssignment(Node):
    def __init__(self, obj, member, value):
        self.obj = obj
        self.member = member
        self.value = value

class IndexAssignment(Node):
    def __init__(self, obj, index, value):
        self.obj = obj
        self.index = index
        self.value = value

# ── GUI Nodes ──────────────────────────────────────────────────────────────────

class WindowStmt(Node):
    """window "Title" width W height H [color "bg"] [id "name"] [on_key fn]"""
    def __init__(self, title, width, height, color=None, resizable=True,
                 widget_id=None, on_key=None):
        self.title   = title
        self.width   = width
        self.height  = height
        self.color   = color
        self.resizable = resizable
        self.widget_id = widget_id
        self.on_key  = on_key

class LabelStmt(Node):
    """label "text" at X Y [font_size N] [color "c"] [id "name"]"""
    def __init__(self, text, x, y, font_size=None, color=None, widget_id=None):
        self.text      = text
        self.x         = x
        self.y         = y
        self.font_size = font_size
        self.color     = color
        self.widget_id = widget_id

class ButtonStmt(Node):
    """button "text" at X Y [width W] [height H] [on_click func_name] [color "c"] [id "name"]"""
    def __init__(self, text, x, y, width=None, height=None,
                 on_click=None, color=None, widget_id=None, on_key=None):
        self.text      = text
        self.x         = x
        self.y         = y
        self.width     = width
        self.height    = height
        self.on_click  = on_click
        self.color     = color
        self.widget_id = widget_id
        self.on_key    = on_key

class InputStmt(Node):
    """input "id" at X Y [width W] [placeholder "text"] [password]"""
    def __init__(self, widget_id, x, y, width=None, placeholder=None,
                 password=False, on_key=None):
        self.widget_id   = widget_id
        self.x           = x
        self.y           = y
        self.width       = width
        self.placeholder = placeholder
        self.password    = password
        self.on_key      = on_key

class ImageStmt(Node):
    """image "path" at X Y [width W] [height H]"""
    def __init__(self, path, x, y, width=None, height=None):
        self.path   = path
        self.x      = x
        self.y      = y
        self.width  = width
        self.height = height

class TextboxStmt(Node):
    """textbox "id" at X Y width W height H"""
    def __init__(self, widget_id, x, y, width, height, on_key=None):
        self.widget_id = widget_id
        self.x         = x
        self.y         = y
        self.width     = width
        self.height    = height
        self.on_key    = on_key

class CheckboxStmt(Node):
    """checkbox "id" text "label" at X Y [on_change func]"""
    def __init__(self, widget_id, text, x, y, on_change=None):
        self.widget_id = widget_id
        self.text      = text
        self.x         = x
        self.y         = y
        self.on_change = on_change

class DropdownStmt(Node):
    """dropdown "id" options ["a","b"] at X Y [on_change func]"""
    def __init__(self, widget_id, options, x, y, on_change=None):
        self.widget_id = widget_id
        self.options   = options
        self.x         = x
        self.y         = y
        self.on_change = on_change

class SetTextStmt(Node):
    """set_text "id" to expr"""
    def __init__(self, widget_id, value):
        self.widget_id = widget_id
        self.value     = value

class GetTextStmt(Node):
    """get_text "id"  → returns string value"""
    def __init__(self, widget_id):
        self.widget_id = widget_id

# Alias: get_text used in expression position
GetTextExpr = GetTextStmt

class ShowWindowStmt(Node):
    """show_window  — starts the GUI event loop"""
    pass

class AlertStmt(Node):
    """alert "message"  — popup dialog"""
    def __init__(self, message):
        self.message = message

class SetColorStmt(Node):
    """set_color "id" to "color" """
    def __init__(self, widget_id, color):
        self.widget_id = widget_id
        self.color     = color

class SetVisibleStmt(Node):
    """set_visible "id" true/false"""
    def __init__(self, widget_id, visible):
        self.widget_id = widget_id
        self.visible   = visible

# ── Creative/Canvas Nodes ─────────────────────────────────────────────────────

class CanvasStmt(Node):
    """canvas "id" width W height H [color "bg"] [on_key fn]"""
    def __init__(self, widget_id, width, height, color=None, on_key=None):
        self.widget_id = widget_id
        self.width  = width
        self.height = height
        self.color  = color
        self.on_key = on_key

class DrawStmt(Node):
    """draw shape on "canvas_id" with x1 y1 x2 y2 ... [color "c"] [width N] [fill "c"]"""
    def __init__(self, shape, canvas_id, coords, color=None, fill=None, outline_width=None, text=None):
        self.shape     = shape      # line | rectangle | oval | circle | text | polygon | arc
        self.canvas_id = canvas_id
        self.coords    = coords     # list of expression nodes
        self.color     = color
        self.fill      = fill
        self.outline_width = outline_width
        self.text      = text

class ClearCanvasStmt(Node):
    """clear_canvas "id\""""
    def __init__(self, canvas_id):
        self.canvas_id = canvas_id

class SliderStmt(Node):
    """slider "id" from A to B at X Y [on_change func]"""
    def __init__(self, widget_id, minimum, maximum, x, y, on_change=None):
        self.widget_id = widget_id
        self.minimum   = minimum
        self.maximum   = maximum
        self.x         = x
        self.y         = y
        self.on_change = on_change

class ProgressStmt(Node):
    """progress "id" value V at X Y width W"""
    def __init__(self, widget_id, x, y, width=None):
        self.widget_id = widget_id
        self.x         = x
        self.y         = y
        self.width     = width

class TimerStmt(Node):
    """every N milliseconds call func_name — repeating timer"""
    def __init__(self, interval, handler, in_seconds=False):
        self.interval = interval
        self.handler  = handler
        self.in_seconds = in_seconds

class AfterStmt(Node):
    """after N milliseconds call func_name — one-shot delay"""
    def __init__(self, delay, handler, in_seconds=False):
        self.delay   = delay
        self.handler = handler
        self.in_seconds = in_seconds

class BeepStmt(Node):
    """beep [frequency Hz] [duration ms]"""
    def __init__(self, frequency=None, duration=None):
        self.frequency = frequency
        self.duration  = duration

class GetSliderStmt(Node):
    """get_slider "id" → current numeric value (alias of get_text)"""
    def __init__(self, widget_id):
        self.widget_id = widget_id

class SetProgressStmt(Node):
    """set_progress "id" to value"""
    def __init__(self, widget_id, value):
        self.widget_id = widget_id
        self.value     = value