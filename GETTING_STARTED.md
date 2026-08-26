# e++ Getting Started Guide

## What is e++?

e++ is a beginner-friendly programming language designed to be **the easiest language to learn in the world**. It uses English-like syntax that reads naturally — and it ships with a built-in desktop GUI framework, canvas drawing and animation.

---

## Where to Write e++ Code

### Option 1: E++ IDE (Recommended for Beginners)

The E++ IDE provides a complete development environment with:
- Syntax highlighting + **autocomplete** (press `Ctrl+Space`)
- File explorer
- One-click Run (`F5`)
- Output terminal with automatic error-line highlighting
- **Examples gallery** built in
- Light/dark theme toggle

**To start the IDE:**
```bash
cd epp-ide
npm install
npm start
```

### Option 2: Any Text Editor

Write code anywhere and save with the `.epp` extension, e.g. `myscript.epp`.

### Option 3: Command Line (with REPL)

```bash
# Run a program
python3 -m interpreter.epp your_program.epp

# Evaluate a one-liner
python3 -m interpreter.epp -e 'say "quick math: {2 ^ 10}"'

# Start an interactive REPL — just type e++!
python3 -m interpreter.epp

# Developer tools
python3 -m interpreter.epp --check file.epp    # syntax check (used by the IDE)
python3 -m interpreter.epp --tokens file.epp   # show tokens
python3 -m interpreter.epp --ast file.epp      # show syntax tree
```

REPL commands: `help`, `vars`, `clear`, `exit`.

---

## Basic Syntax Guide

### 1. Comments
```epp
# hash comment
// slash comment
```

### 2. Variables & Compound Assignment
```epp
name = "Alice"
age = 25
score = 10
score += 5    # also -= *= /= %=
```

### 3. Printing & String Interpolation
```epp
say "Hello!"
say "Hi {name}, next year you'll be {age + 1}!"
```
Anything inside `{...}` is evaluated — and you can format the result after a colon:
```epp
pi = 3.14159
user = {"name": "Zoe"}
say "Hi {user['name']}! pi ≈ {pi:.2f}, id: {42:05d}"
```

### Membership: `in` / `not in`
```epp
fruits = ["apple", "banana"]
if "apple" in fruits:
    say "yes!"
say "kiwi" not in fruits     # true
```

### 4. Getting User Input
```epp
name = input("What is your name? ")
say "Hello, {name}!"
```

### 5. Math Operations
```epp
a = 10 + 5
b = 2 ^ 10      # power → 1024
c = 17 % 5      # modulo → 2
d = 15 / 3      # division → 5 (whole results stay whole)
```

### 6. Comparisons — English OR symbols, your choice
```epp
if x > 10 and x != 15:            # or: x is greater than 10 / is not equal to
    say "big"

if name == "Alice":               # or: name is equal to "Alice"
    say "hi!"

if score >= 60:                   # or: score is greater than or equal to 60
    say "passed"
```

### 7. If/Elif/Else
```epp
if score >= 90:
    say "A"
elif score >= 80:
    say "B"
else:
    say "keep trying"
```

### 8. Loops — three flavours plus break/continue
```epp
for i in range(5):
    say i

repeat 3 times:
    say "echo"

count = 0
while count < 5:
    count += 1

for c in "abc":
    if c == "b":
        continue     # skip b
    say c
```

### 9. Switch
```epp
switch day:
    case "Saturday", "Sunday":
        say "weekend!"
    default:
        say "workday"
```

### 10. Functions
```epp
func add(a, b):
    return a + b

result = add(5, 3)          # parentheses style
read_file "notes.txt"       # string-first functions have shorthand
write_file "out.txt", "hi"  # extra args after a comma
```

### 11. Lists & Dictionaries with real indexing
```epp
numbers = [1, 2, 3, 4, 5]
say numbers[0]         # first
say numbers[-1]        # last (negative indexing!)
numbers[2] = 99

person = {
    "name": "Alice",
    "age": 25
}
say person["name"]
person["city"] = "Paris"

matrix = [[1, 2], [3, 4]]
say matrix[1][0]       # 3 — chained indexing
```

Handy methods: `.push(x)` `.pop()` `.contains(x)` `.index_of(x)` `.first()` `.last()` `.sort()` `.reverse()`, strings get `.upper()` `.lower()` `.trim()` `.split(sep)` `.replace(a, b)` and more.

### 12. Classes — methods take arguments properly
```epp
class Animal:
    func init(name, sound):
        self.name = name
        self.sound = sound
    func speak_to(other):
        return "{self.name}: {self.sound} at {other.name}"

dog = Animal("Rex", "Woof")
cat = Animal("Tom", "Meow")
say dog.speak_to(cat)
```

### 13. Try/Catch — robust error handling
```epp
try:
    result = 10 / 0
catch err:
    say "Oops: {err}"

try:
    risky_thing()        # catch block is optional
say "moving on..."
```
`return` works correctly inside try blocks.

### 14. Imports
```epp
import "utils.epp"
```
Files are resolved relative to the importing file; each file runs once; circular imports fail with a friendly message.

---

## Keyboard Games

```epp
window "Game" width 440 height 480 color "#0d0d1a" on_key handle_key
canvas "cv" width 400 height 400 color "#111122"

func handle_key(key):
    if key == "Left" or key == "a":
        move_left()
    elif key == "Right" or key == "d":
        move_right()

every 120 milliseconds call tick
show_window
```
Key names: `"Left"` `"Right"` `"Up"` `"Down"`, letter keys like `"a"`, and `"space"`.
See the complete Snake game in `tests/examples/snake.epp`!

## GUI Apps

```epp
window "My App" width 400 height 300 color "#f8f8f8"

label "Enter your name:" at 20 20
input "box" at 20 50 width 220 placeholder "type here..."
slider "vol" from 0 to 100 at 20 90 on_change vol_changed
progress "bar" at 20 130 width 300
button "Greet" at 20 170 width 150 height 45 on_click greet color "lightblue"

func vol_changed():
    set_progress "bar" to get_text "vol"

func greet():
    alert "Hello {get_text('box')}!"

show_window
```

Widgets: `window` `label` `button` `input` `textbox` `checkbox` `dropdown` `slider` `progress` `image`.
Commands: `set_text ... to ...`, `get_text "id"`, `set_color ... to ...`, `set_visible`, `set_progress ... to ...`, `alert`, `beep`.

> Note: words like `text`, `color`, `width` are *soft keywords* — they work as normal variable names too: `text = "hello"` is fine!

## Canvas Drawing & Animation

```epp
window "Stars" width 500 height 400 color "black"
canvas "cv" width 480 height 360 color "black"

every 100 milliseconds call twinkle

func twinkle():
    draw dot on "cv" at random_int(0, 480) random_int(0, 360) color "white"

show_window
```

Draw shapes: `draw line/rectangle/circle/dot/text on "cv" ...`, clear with `clear_canvas "cv"`. Time things with `every N milliseconds call fn` (repeating) or `after N milliseconds call fn` (once).

## Networking & JSON
```epp
data = fetch_json("https://api.github.com/users/octocat")
say data["login"]

config = {"theme": "dark"}
write_file "config.json", to_json(config)
loaded = parse_json(read_file "config.json")
```

---

## Built-in Functions (Quick Reference)

| Category | Functions |
|----------|-----------|
| I/O | `say`, `input` |
| Types | `type str int float bool` |
| Collections | `len range push pop keys values contains index_of sort reversed sum slice` |
| Strings | `split join trim replace upper lower` |
| Math | `abs round floor ceil pow sqrt min max` |
| Files | `read_file write_file append_file exists delete_file` |
| System | `random random_int shuffle time clock sleep` |
| Web | `fetch fetch_json parse_json to_json` |

---

## Complete Example Program

```epp
# Modern e++ demo
func factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

class Person:
    func init(name, age):
        self.name = name
        self.age = age
    func introduce():
        say "Hi, I'm {self.name}, {self.age}"

say "=== e++ Demo ==="
name = input("Your name? ")

say "Factorial of 5: {factorial(5)}"
p = Person(name, 25)
p.introduce()

if p.age >= 18:
    say "adult"
else:
    say "minor"

for i in range(5):
    say "Number: {i + 1}"
```

---

## Tips for Beginners

1. **Use 4 spaces for indentation**
2. **Save files with `.epp` extension**
3. **Use `say` and `{interpolation}` to debug**
4. **Read error messages** — they show the line number and usually a fix suggestion; the IDE even highlights the line for you
5. **Press Ctrl+Space in the IDE** for autocomplete of every function
6. **Open Examples** in the IDE for ready-made programs (games, art, timers!)

## File Locations

| Item | Location |
|------|----------|
| CLI Interpreter | `python3 -m interpreter.epp` (or bundled `dist/epp`) |
| Example Programs | `tests/examples/` |
| Language Spec | `LANGUAGE_SPEC.md` |
| AI config | `epp-ide/config.json.example` |

## Getting Help

- Read `LANGUAGE_SPEC.md` for the complete language reference
- Check example programs in `tests/examples/`
