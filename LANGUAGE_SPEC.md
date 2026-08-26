# e++ Language Specification (v2.3)

## Overview

e++ (pronounced "e plus plus") is a beginner-friendly programming language designed to be the easiest language to learn in the world. It features English-like syntax, indentation-based structure, modern programming constructs, a built-in desktop GUI framework, and canvas drawing/animation.

**Design Goals:**
- Readable like English prose
- Familiar constructs from mainstream languages
- Minimal boilerplate, maximum clarity
- Friendly error messages for beginners

## Basics

### Hello World
```epp
say "Hello, World!"
```

### Comments
```epp
# This is a hash comment
// This is also a comment
```

### Variables
Variables are dynamically typed and mutable.
```epp
name = "Alice"
age = 25
pi = 3.14
is_active = true
empty = null

# Compound assignment works too
score = 10
score += 5    # same as score = score + 5
score -= 3
score *= 2
score /= 4
score %= 7
```

### Data Types

| Type | Example | Description |
|------|---------|-------------|
| `int` | `42`, `-7` | Whole numbers |
| `float` | `3.14`, `-0.5` | Decimal numbers |
| `string` | `"Hello"` | Text enclosed in quotes |
| `bool` | `true`, `false` | Logical values |
| `list` | `[1, 2, 3]` | Ordered collection |
| `dict` | `{"name": "Bob", "age": 30}` | Key-value pairs |
| `null` | `null` | Empty or no value |

### Printing Output & String Interpolation
```epp
say "Hello!"
say "Value: " + 42

# Interpolation: put any expression inside {curly braces}
name = "World"
say "Hello, {name}!"                 # Hello, World!
say "2 + 2 is {2 + 2}"               # 2 + 2 is 4
user = {"name": "Zoe"}
say "Hi {user['name'].upper()}!"     # Hi ZOE!

# Format specs after a colon (Python-style)
pi = 3.14159
say "pi ≈ {pi:.2f}"                  # pi ≈ 3.14
say "id: {42:05d}"                   # id: 00042
say "{1234567:,}"                    # 1,234,567
```
> Tip: use single quotes for strings inside `{}` — nested double quotes are not allowed.

### Getting Input
```epp
name = input("Enter your name: ")
say "Hello, {name}!"

age = int(input("Age: "))
if age >= 18:
    say "adult"
```

## Operators

### Arithmetic
```epp
a = 10 + 5    # addition (also joins strings)
b = 10 - 3    # subtraction
c = 4 * 2     # multiplication
d = 15 / 3    # division (whole results stay whole: 15 / 3 → 5)
e = 17 % 5    # modulo (remainder) → 2
f = 2 ^ 10    # power → 1024
```

### Comparison (English AND symbols both work)
```epp
if x > 10:                    # or: x is greater than 10
if name == "Alice":           # or: name is equal to "Alice"
if age < 18:                  # or: age is less than 18
if score >= 60:               # or: score is greater than or equal to 60

x = 5 != 3                    # true   (or: 5 is not equal to 3)
y = 4 <= 4                    # true   (or: 4 is less than or equal to 4)
z = "a" is not "b"            # true

# Membership: 'in' and 'not in' work on lists, strings and dicts
if "apple" in fruits:
    say "we have apples"
if user["name"] not in banned:
    say "welcome!"
```

### Boolean Logic
```epp
if x > 10 and x != 15:
    say "valid"

if is_sunny or is_warm:
    say "nice day"

if not is_raining:
    say "go outside"
```
Precedence (loosest to tightest): `or` → `and` → comparisons → `+ -` → `* / % ^` → `not` / unary `-`.

### Truthy/Falsy
Python-like rules apply:
- `false`, `0`, `""`, `[]`, `{}`, `null` are **falsy**
- Everything else is **truthy**

```epp
if my_list:         # true if list is not empty
    say "has items"
```

## Control Flow

### If / Elif / Else
```epp
if temperature > 30:
    say "hot"
elif temperature > 20:
    say "comfortable"
else:
    say "cool"
```

### For Loop
```epp
for i in range(5):
    say i

fruits = ["apple", "banana", "cherry"]
for fruit in fruits:
    say fruit
```

### Repeat Loop
```epp
repeat 3 times:
    say "echo"
countdown = 5
repeat countdown times:
    say "tick"
```

### While Loop
```epp
count = 0
while count < 5:
    say count
    count += 1
```

### Break & Continue
```epp
for i in range(10):
    if i == 3:
        continue      # skip this iteration
    if i == 6:
        break         # leave the loop entirely
    say i             # prints 0 1 2 4 5
```

### Switch
Cases can list multiple values separated by commas; `default` runs when nothing matches. Each case is exclusive — no fall-through.
```epp
switch day:
    case "Saturday", "Sunday":
        say "weekend!"
    case "Friday":
        say "almost there"
    default:
        say "workday"
```

### Try / Catch
The catch variable is optional, and so is the whole catch block. `return` inside a try block works correctly.
```epp
try:
    result = 10 / 0
catch error:
    say "Error occurred: {error}"

try:
    risky()
catch:
    say "something went wrong"

try:
    log("checkpoint")     # errors here are simply ignored
```

## Functions

### Defining Functions
```epp
func greet(name):
    say "Hello, {name}!"

func add(a, b):
    return a + b

func square(x):
    return x ^ 2
```

### Calling Functions
Parentheses are the normal style. Functions whose first argument is a string also support a bare shorthand:
```epp
greet("World")
result = add(5, 3)

read_file "notes.txt"                  # same as read_file("notes.txt")
write_file "out.txt", "hello there"    # extra args follow a comma
```

### Built-in Functions

**Output/Input:**
- `say(value)` — Print to output
- `input(prompt)` — Get user input

**Type Conversion:**
- `type(x)` · `str(x)` · `int(x)` · `float(x)` · `bool(x)`

**Collections:**
- `len(x)` · `range(n)` / `range(start, stop, step)` · `push(list, item)` · `insert(list, index, item)` · `pop(list)`
- `contains(container, item)` · `index_of(list, item)`
- `sort(list)` (returns sorted copy) · `reversed(list_or_string)` · `sum(numbers)` · `slice(seq, start, end)`
- `keys(dict)` · `values(dict)`

**Strings:**
- `split(str, delimiter)` · `join(list, delimiter)` · `trim(str)` · `replace(str, old, new)`
- `upper(str)` · `lower(str)`

**Files:**
- `read_file(path)` · `write_file(path, content)` · `append_file(path, content)`
- `exists(path)` · `delete_file(path)`

**Math:**
- `abs(n)` · `round(n, digits?)` · `floor(n)` · `ceil(n)` · `pow(a, b)` · `sqrt(n)` · `min(...)` · `max(...)`

**System:**
- `random()` · `random_int(lo, hi)` · `shuffle(list)` · `time()` · `clock()` · `sleep(seconds)`

**Networking & JSON:**
- `fetch(url)` — raw response text
- `fetch_json(url)` — parsed JSON in one step
- `parse_json(text)` · `to_json(obj)`

### Built-in Methods on Values
```epp
nums = [3, 1, 2]
nums.push(4)          nums.insert(0, x)   nums.unshift(x)   nums.pop()   nums.len()
nums.contains(1)      nums.index_of(2)  nums.first()  nums.last()
nums.sort()           nums.reverse()

s = "Hello"
s.upper()   s.lower()   s.trim()    s.contains("ell")
s.starts_with("He")     s.ends_with("lo")
s.replace("l", "L")     s.split("l")    s.index_of("o")   s.len()

d = {"a": 1}
d.keys()    d.values()  d.contains("a")   d.get("a")        d.get("x", 0)
d.remove("a")           d.len()
```

## Indexing

Lists and strings index from 0; negative indexes count from the end. Dicts are indexed by key. Chained indexing and assignment work everywhere.
```epp
nums = [10, 20, 30]
say nums[0]          # 10
say nums[-1]         # 30
nums[1] = 99

matrix = [[1, 2], [3, 4]]
say matrix[1][0]     # 3

person = {"name": "Ada"}
say person["name"]   # Ada
person["age"] = 36

word = "e++"
say word[0]          # e
```

## Classes

Methods take arguments like regular functions, and constructors validate their argument count.
```epp
class Animal:
    func init(name, sound):
        self.name = name
        self.sound = sound

    func speak():
        return "{self.name} says {self.sound}"

    func speak_to(other):
        return self.sound + " at " + other.name

dog = Animal("Rex", "Woof")
cat = Animal("Tom", "Meow")
say dog.speak()
say dog.speak_to(cat)
```

## Import

```epp
import "utils.epp"
```
Search order: the importing file's folder, then the interpreter's `lib/` folder. Each file executes only once per run, and circular imports are detected with a friendly error.

## Desktop GUI Framework

GUI programs build widgets top-to-bottom and end with `show_window`.
```epp
window "My App" width 400 height 300 color "white" id "win"

label "Enter your name:" at 20 20 font_size 14
input "name_box" at 20 50 width 200 placeholder "type here..." password?
button "Go" at 20 90 width 120 height 40 on_click go color "lightgray" id "gobtn"
checkbox "agree" text "I agree" at 20 150 on_change toggle
dropdown "choice" options ["Red", "Green"] at 20 180 on_change pick
textbox "notes" at 20 210 width 300 height 100
image "logo.png" at 240 20 width 100 height 100
slider "vol" from 0 to 100 at 20 330 on_change volume
progress "bar" at 250 330 width 120

func go():
    alert "Hello {get_text('name_box')}!"
    set_text "gobtn" to "Clicked!"
    set_color "win" to "#ffeecc"
    set_visible "gobtn" false

show_window
```

Widget reference:

| Statement | Parameters |
|-----------|-----------|
| `window` | `"Title"` `width` `height` `[color]` `[resizable]` `[id]` `[on_key fn]` |
| `label` | `"text"` `at X Y` `[font_size N]` `[color]` `[id]` |
| `button` | `"text"` `at X Y` `[width]` `[height]` `[on_click fn]` `[color]` `[id]` `[on_key fn]` |
| `input` | `"id"` `at X Y` `[width]` `[placeholder "..."]` `[password]` `[on_key fn]` |
| `image` | `"path"` `at X Y` `[width]` `[height]` |
| `textbox` | `"id"` `at X Y` `[width]` `[height]` `[on_key fn]` |
| `checkbox` | `"id"` `[text "..."]` `at X Y` `[on_change fn]` |
| `dropdown` | `"id"` `options [...]` `at X Y` `[on_change fn]` |
| `slider` | `"id"` `[from A]` `[to B]` `at X Y` `[on_change fn]` |
| `canvas` | `"id"` `[width W]` `[height H]` `[color "bg"]` `[on_key fn]` |
Commands: `set_text "id" to v` · `v = get_text "id"` · `set_color "id" to "red"` · `set_visible "id" false` · `set_progress "id" to 50` · `alert "msg"` · `beep [freq] [ms]` · `show_window`

## Canvas Drawing & Animation

```epp
window "Demo" width 420 height 340 color "black"
canvas "cv" width 400 height 300 color "midnightblue"

draw line on "cv" from 0 0 to 400 300 color "cyan" width 2
draw rectangle on "cv" from 20 20 to 120 120 color "white" fill "gray"
draw circle on "cv" at 200 150 size 50 color "yellow" fill "orange"
draw dot on "cv" at 300 80 color "pink"
draw text on "cv" at 30 280 text "Hello canvas!" color "white"
clear_canvas "cv"

every 100 milliseconds call tick      # repeating timer
after 2000 milliseconds call boom     # one-shot timer

func tick():
    draw dot on "cv" at random_int(0, 400) random_int(0, 300) color "white"

func boom():
    beep 880 200
    alert "boom!"

show_window
```

Shapes: `line` (`from X1 Y1 to X2 Y2`) · `rectangle` (`from ... to ...`, alias `rect`/`box`) · `circle`/`oval`/`dot` (`at CX CY size R`) · `text` (`at X Y text "..."`). Options: `[color "c"] [fill "c"] [width N]`.

## Error Messages

Errors point at the offending line **and column**, and usually include a suggestion. Runtime errors carry the position of the expression that failed, even inside functions:
```
Error at line 3, column 20: 'naame' is not defined — Did you forget to assign it?
Error at line 7, column 9: List index 5 out of range (length 3)
Error at line 12: Cannot divide by zero
Error at line 2, column 5: I expected a value here but found end of line
Error: Circular import detected: 'a.epp' imports itself
```
The IDE highlights the line automatically after a failed run — and shows live squiggles as you type (see below).

## Built-in Testing

Write tests right in your programs with `test` blocks and `expect`:
```epp
func add(a, b):
    return a + b

test "addition works":
    expect add(2, 2) to_be 4
    expect add(-1, 1) to_be 0

test "membership":
    expect "ell" in "Hello" to_be_true

test "floats are forgiving":
    expect 0.1 + 0.2 to_be 0.3      # tiny float tolerance built in

test "errors can be verified":
    expect 1 / 0 to_throw
```

Matchers:
| Matcher | Passes when... |
|---------|----------------|
| `expect X to_be Y` | X equals Y (numbers compare with tiny tolerance) |
| `expect X to_be_true` | X is truthy |
| `expect X to_be_false` | X is falsy |
| `expect X() to_throw` | evaluating X raises an error |

Results print as they run with a final summary, and the interpreter exits with code 1 if anything failed — perfect for CI:
```
▶ test: addition works
  (2 checks ran)

✔ TESTS: all 3 passed
```

## Command-line Tools

```bash
python3 -m interpreter.epp program.epp        # run
python3 -m interpreter.epp                    # REPL
python3 -m interpreter.epp -e 'say 2 ^ 8'     # one-liner
python3 -m interpreter.epp --test file.epp    # run tests, exit 1 on failure
python3 -m interpreter.epp --check file.epp   # parse-only check (exit code 1 on error)
python3 -m interpreter.epp --check file.epp --json   # machine-readable output for tools
python3 -m interpreter.epp --tokens file.epp  # dump the token stream (debugging)
python3 -m interpreter.epp --ast file.epp     # dump the syntax tree (debugging)
```
`--check` is what powers the IDE's live error squiggles.

## Reserved Words

Hard keywords (never usable as names):
```
func class if elif else for while return say break continue
in and or not null true false self import try catch
repeat times switch case default
```
Soft keywords (contextual — usable as ordinary variables too):
```
input window label button image textbox checkbox dropdown canvas slider progress
alert show_window set_text set_color set_visible set_progress get_text clear_canvas
draw every after call beep on with from to at size fill text options
at width height color font_size id placeholder password resizable on_click on_change
milliseconds ms second seconds
```

## Grammar Summary

See `grammar.ebnf` for the full grammar. Notable productions:
```
statement     → func_def | class_def | if_stmt | repeat_stmt | switch_stmt
              | while_stmt | for_stmt | try_catch | gui_stmt | canvas_stmt
              | return_stmt | import_stmt | expr_stmt
switch_stmt   → "switch" expr ":" INDENT case_block* default_block? DEDENT
repeat_stmt   → "repeat" expr "times" ":" block
expr          → assignment (right-assoc, supports += -= *= /= %=)
assignment    → target assign_op expr
comparison    → term (("is"|"=="|">"|...) term)*
```

## File Extension

All e++ source files use the extension: `.epp`
