# stredit
A little language that edits strings.

stredit is a string editor. It takes two strings, one is the program (a string) and the other is the data (a string). 
The program string is a series of commands that are applied to the data string, until the program ends or the end of 
the data is discovered. 

Key concept: Each command is a single character. It's a bit like a turing machine, in that it has a
program tape and a data tape. Each command processes one character of the data at a time.

This program converts a string to upper-case
```python
*^>
```

Always 'vocalise' a program to understand it. So, the above is: 
"(*) loop (^) toupper (>) moveright"

This program converts the first word to upper case, then deletes the rest
of the string.
```python
{*?w^>}{*d}
```

"block loop if word toupper moveright endblock block loop delete endblock"

There are plenty of breadcrumbs in the python to help you get started.

There is a trinket here you can play with now: https://trinket.io/python3/0b9355c93f

If you just run the stredit module, you get an interactive shell.

```python
python stredit.py
prog> *^>
data>hello world
HELLO WORLD
           ^
data>

```
Press RETURN at the data prompt to get back to the prog prompt.
Press RETURN at the prog prompt to exit the test shell.

Or you can build your own main.py that gives you a way to access the built-in
help and reference pages.

Run/Edit main.py and follow your nose from there, because main.py uses
the run() command line mode of stredit to provide you with a prompt, and it is
an ideal way to interactively test your programs.

```python
# main.py
from stredit import *

# uncomment specific lines to get help
#help()         # generic help
#examples()     # show lots of useful cookbook examples
#commands()     # a command reference
#charsets()     # a reference to the available charsets

# set debug=True to get an instruction and data trace
run(debug=False)
```

# Using stredit in your programs
stredit is open source, so as long as you leave the LICENCE file intact, you can
do what ever you want with this program.

## Embedding stredit into your program

The edit() method does all the hard work for you.
Just pass your data and a program string to it, and use the results
that it returns.

```
import stredit
data = input("string to edit? ")
result, pos = stredit.edit(data, prog)
print("result is:%s" % result)
stredit.point(result, pos)  # another way to show results
```

## Building an executable

You can turn a python program into an executable with pyinstaller:

https://https://www.pyinstaller.org/


David Whale

@whaleygeek

December 2021
