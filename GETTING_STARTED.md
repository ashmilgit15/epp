# e++ Getting Started Guide

## What is e++?

e++ is a beginner-friendly programming language designed to be **the easiest language to learn in the world**. It uses English-like syntax that reads naturally.

---

## Where to Write e++ Code

### Option 1: E++ IDE (Recommended for Beginners)

The E++ IDE provides a complete development environment with:
- Syntax highlighting
- File explorer
- Run button
- Output terminal

**To start the IDE:**
```bash
cd epp-ide/release/linux-unpacked
./epp-ide
```

### Option 2: Any Text Editor

You can write e++ code in any text editor:
- VS Code
- Notepad
- Sublime Text
- Nano/Vim
- Any plain text editor

**Save your file with `.epp` extension**, e.g., `myscript.epp`

### Option 3: Command Line

Create and run directly from terminal:
```bash
echo 'say "Hello!"' > hello.epp
./dist/epp hello.epp
```

---

## How to Run e++ Programs

### Using the Executable
```bash
./dist/epp your_program.epp
```

### Using Python
```bash
python3 -m interpreter.epp your_program.epp
```

---

## Basic Syntax Guide

### 1. Comments
```epp
# This is a comment
# Comments are ignored by the interpreter
```

### 2. Variables
```epp
# No type declarations needed
name = "Alice"
age = 25
height = 5.8
is_student = true
nothing = null
```

### 3. Printing Output
```epp
say "Hello, World!"
say "Your age is: " + 25
```

### 4. Getting User Input
```epp
name = input("What is your name? ")
say "Hello, " + name
```

### 5. Math Operations
```epp
a = 10 + 5    # Addition
b = 10 - 3    # Subtraction
c = 4 * 2     # Multiplication
d = 15 / 3    # Division
```

### 6. String Concatenation
```epp
first = "Hello"
second = "World"
full = first + " " + second    # "Hello World"
```

### 7. Comparisons (English-like!)
```epp
if x is greater than 10:
    say "big"

if x is less than 5:
    say "small"

if x is equal to 10:
    say "exact"

if x is not 0:
    say "not zero"

if x is greater than or equal to 10:
    say "at least 10"

if x is less than or equal to 5:
    say "at most 5"
```

### 8. Boolean Logic
```epp
if x is greater than 0 and x is less than 10:
    say "single digit positive"

if is_sunny or is_warm:
    say "nice weather"

if not is_raining:
    say "no umbrella needed"
```

### 9. If/Elif/Else
```epp
if score is greater than or equal to 90:
    say "Grade: A"
elif score is greater than or equal to 80:
    say "Grade: B"
elif score is greater than or equal to 70:
    say "Grade: C"
else:
    say "Grade: F"
```

### 10. For Loops
```epp
# Loop from 0 to 4
for i in range(5):
    say i

# Loop through a list
fruits = ["apple", "banana", "cherry"]
for fruit in fruits:
    say fruit
```

### 11. While Loops
```epp
count = 1
while count is less than or equal to 5:
    say count
    count = count + 1
```

### 12. Functions
```epp
# Define a function
func greet(name):
    say "Hello, " + name

# Call the function
greet("Alice")
greet("Bob")

# Function with return value
func add(a, b):
    return a + b

result = add(5, 3)
say result    # prints 8
```

### 13. Recursion
```epp
func factorial(n):
    if n is less than or equal to 1:
        return 1
    return n * factorial(n - 1)

say factorial(5)    # prints 120
```

### 14. Lists
```epp
# Create a list
numbers = [1, 2, 3, 4, 5]

# Access elements
say numbers[0]      # prints 1

# Add element
push(numbers, 6)

# Remove last element
last = pop(numbers)

# Length
say len(numbers)
```

### 15. Dictionaries (Key-Value Pairs)
```epp
# Create a dictionary
person = {"name": "Alice", "age": 25}

# Access values
say person["name"]    # prints Alice
say person["age"]     # prints 25

# Get keys and values
say keys(person)
say values(person)
```

### 16. Classes
```epp
class Animal:
    func init(name):
        self.name = name
    
    func speak():
        say self.name + " makes a sound"

# Create an instance
dog = Animal("Rex")
dog.speak()           # prints "Rex makes a sound"

# Access properties
say dog.name          # prints "Rex"
```

### 17. Try/Catch (Error Handling)
```epp
try:
    result = 10 / 0
catch error:
    say "Error: " + error
```

### 18. Importing Files
```epp
# Import another e++ file
import "utils.epp"

# Now you can use functions from utils.epp
```

---

## Built-in Functions

| Function | Description | Example |
|----------|-------------|---------|
| `say(x)` | Print output | `say "hello"` |
| `input(prompt)` | Get user input | `name = input("Name: ")` |
| `type(x)` | Get type name | `type(42)` → `"int"` |
| `len(x)` | Get length | `len([1,2,3])` → 3 |
| `range(n)` | Create range | `range(5)` → `[0,1,2,3,4]` |
| `str(x)` | Convert to string | `str(42)` → `"42"` |
| `int(x)` | Convert to int | `int("42")` → 42 |
| `float(x)` | Convert to float | `float("3.14")` → 3.14 |
| `bool(x)` | Convert to bool | `bool(0)` → false |
| `push(list, item)` | Add to list | `push(nums, 5)` |
| `pop(list)` | Remove last | `pop(nums)` |
| `keys(dict)` | Get dict keys | `keys(d)` |
| `values(dict)` | Get dict values | `values(d)` |
| `read_file(path)` | Read file | `read_file("test.txt")` |
| `write_file(path, content)` | Write file | `write_file("out.txt", "hi")` |
| `exists(path)` | Check file exists | `exists("data.txt")` |
| `random()` | Random number 0-1 | `random()` |
| `time()` | Current timestamp | `time()` |
| `sleep(seconds)` | Pause execution | `sleep(1)` |

---

## Complete Example Program

```epp
# e++ Example Program

# Function to calculate factorial
func factorial(n):
    if n is less than or equal to 1:
        return 1
    return n * factorial(n - 1)

# Class to represent a person
class Person:
    func init(name, age):
        self.name = name
        self.age = age
    
    func introduce():
        say "Hi, I'm " + self.name
        say "I'm " + self.age + " years old"
    
    func is_adult():
        return self.age is greater than or equal to 18

# Main program
say "=== e++ Demo ==="
say ""

# Variables
name = input("Enter your name: ")
say "Hello, " + name + "!"
say ""

# Calculate factorial
say "Factorial of 5: " + factorial(5)
say ""

# Create a person
person = Person(name, 25)
person.introduce()

if person.is_adult():
    say "You are an adult!"
else:
    say "You are a minor."
say ""

# Work with lists
say "Counting from 1 to 5:"
for i in range(5):
    say "  Number: " + (i + 1)
```

---

## Tips for Beginners

1. **Use 4 spaces for indentation** - e++ uses indentation like Python
2. **Save files with `.epp` extension**
3. **Use `say` to debug** - print values to see what's happening
4. **Read error messages carefully** - they tell you the line number and what's wrong
5. **Start simple** - write small programs first, then build up

---

## File Locations

| Item | Location |
|------|----------|
| IDE Executable | `epp-ide/release/linux-unpacked/epp-ide` |
| CLI Interpreter | `dist/epp` |
| Example Programs | `tests/examples/` |
| Language Spec | `LANGUAGE_SPEC.md` |

---

## Getting Help

- Read `LANGUAGE_SPEC.md` for complete language reference
- Check example programs in `tests/examples/`
- Error messages include line numbers and suggestions