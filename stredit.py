#!/usr/bin/env python3
#
# stredit.py  10/12/2021  D.J.Whale
#
# A programmable string editor.

import sys

ZTERM = '\0'

#===== UTILITY FUNCTIONS =======================================================

def insert(buf:list, start:int, count:int)-> None:
    """Insert a number of items inside a buffer, without creating new buffer"""
    for i in range(count):
        buf.insert(start, ' ')

def delete(buf:list, start:int, count:int) -> None:
    """Delete a number of items inside a buffer, without creating new buffer"""
    for i in range(count):
        buf.pop(start)

# CHARSETS
ucase    = str.upper
lcase    = str.lower
isuclet  = str.isupper
islclet  = str.islower
islet    = str.isalpha
isdig    = str.isdigit
isletdig = str.isalnum
istab    = lambda c: c == '\t'
isnl     = lambda c: c in "\r\n"
isspace  = lambda c: c in " \t"
ispunc   = lambda c: c in "(!?.,;:'\"`)"
isid     = lambda c: c.isalnum() or c == '_'
issymbol = lambda c: not isletdig(c) and not istab(c) and not isnl(c) and not isspace(c)

exiting = False

def point(data, dpos:int=0, dlen:int=1) -> None:
    """Print the buffer with an underlined region"""

    print(point_str(data, dpos, dlen))

def point_str(data, dpos:int=0, dlen:int=1) -> str:
    result = []
    if isinstance(data, list):
        data = data[:-1]  # remove zterm
        data = "".join(data)  # to string

    result.append(data)
    result.append('\n')

    if dpos > 0:
        result.append(" " * dpos)
    if dlen > 0:
        result.append("^" * dlen)
    result.append('\n')
    return "".join(result)


#===== STRING EDITOR CORE ======================================================
#-------------------------------------------------------------------------------
# Edits a string in-place, from a list of commands.
# This is basically a modified 2-tape Turing machine, with a push-down stack.
#
# 'data': string to edit.
# 'prog': program to interpret.
# returns: modified string and new cursor pos (str, int)

def edit(data:str, prog:str, debug:bool=False) -> (str, int):
    """Analyse or edit a string in-place, using a simple string program"""
    global exiting

    buf = list(data)
    buf.append(ZTERM)  # simulate C z-term
    exiting = False
    pos = editi(buf, 0, 0, prog + ZTERM, debug=debug)

    # scan for z-term and truncate there
    zpos = buf.index(ZTERM)
    buf = buf[:zpos]
    return "".join(buf), pos

#-------------------------------------------------------------------------------
# Edit a buffer in-place, from a list of commands.
#
# 'data': mutable buffer to edit.
# 'dpos': position in data buffer to start scanning from.
# 'dlen': length of segment in buffer that is editable (0 to auto calc).
# 'prog': program to interpret.
# returns: position of cursor in 'data' at end of edit.
#
# NOTE: This function is designed to be called recursively with the nested
# scope command, and is still efficient in this mode.

def editi(data:list, dpos:int, dlen:int, prog:str, debug:bool=False) -> int:
    global exiting

    cpos       = 0
    rep        = 0
    loops      = 255  # disabled
    loop_start = 0
    if dlen == 0: dlen = len(data)-1  # don't count ZTERM

    while True:
        if debug: point(data, dpos)
        if debug: point(prog, cpos)

        cmd = prog[cpos]
        if cmd in (ZTERM, '}', '#'):
            # END OF PROG OR SEGMENT
            if loops == 255: break  # looping disabled
            # counting a loop
            if loops != 0:
                # finite counting
                loops -= 1
                if loops == 0: break  # end of finite loop

            # restart prog from 0
            cpos = loop_start
            cmd = prog[cpos]
            if debug: point(data, dpos)
            if debug: point(prog, cpos)

        if isdig(cmd):
            # SET REPEAT COUNT
            rep = (10 * rep) + (ord(cmd) - ord('0'))  # shift in decimal value
            cpos += 1
            continue  # don't decrement rep this time round

        elif cmd == '>':
            # MOVE RIGHT
            if rep == 0: rep = 1
            if dpos+rep <= dlen:  # allow right shift into ZTERM
                dpos = dpos + rep
                rep = 0
            else: break  # end of data

        elif cmd == '<':
            # MOVE LEFT
            if rep == 0: rep = 1
            if dpos-rep >= 0:
                dpos = dpos - rep
                rep = 0
            else: break  # beginning of data

        elif cmd == 'b':
            # MOVE TO BEGINNING
            dpos = 0

        elif cmd == 'e':
            # MOVE TO END
            dpos = dlen-1  # point to ZTERM-1

        elif cmd == 'i':
            # INSERT TO RIGHT (by rep)
            if rep == 0: rep = 1
            insert(data, dpos, rep)  # move z-term
            dlen = dlen + rep
            rep = 0

        elif cmd == 'd':
            # DELETE TO RIGHT (by rep)
            if rep == 0: rep = 1
            if rep > dlen-dpos:
                rep = dlen-dpos
                cmd = ZTERM
            delete(data, dpos, rep)  # move term also
            dlen = dlen - rep
            if cmd == ZTERM: break  # end of prog
            rep = 0

        elif cmd == '^':
            # CONVERT TO UPPER CASE
            if data[dpos] == ZTERM: break  # end of data
            data[dpos] = ucase(data[dpos])

        elif cmd == 'v':
            # CONVERT TO LOWER CASE
            if data[dpos] == ZTERM: break  # end of data
            data[dpos] = lcase(data[dpos])

        elif cmd == '~':
            # TOGGLE CASE
            ch = data[dpos]
            if ch == ZTERM: break  # end of data
            if isuclet(ch):  data[dpos] = lcase(ch)
            else:            data[dpos] = ucase(ch)

        elif cmd == '?' or cmd == '!':
            # TEST NEXT CHAR
            if data[dpos] == ZTERM: break  # end of data
            tester = cmd
            cpos += 1
            cmd = prog[cpos]        # char class to match
            if cmd == ZTERM: break  # end of prog
            ch = data[dpos]         # char in data to match against
            ##if ch == ZTERM: break   # end of data

            # CHARSETS
            if   cmd == 'w':  b = islet(ch)
            elif cmd == 'd':  b = isdig(ch)
            elif cmd == 'A':  b = isuclet(ch)
            elif cmd == 'a':  b = islclet(ch)
            elif cmd == 'i':  b = isid(ch)
            elif cmd == 's':  b = isspace(ch)
            elif cmd == 't':  b = istab(ch)
            elif cmd == 'n':  b = isnl(ch)
            elif cmd == 'y':  b = issymbol(ch)
            elif cmd == 'p':  b = ispunc(ch)
            elif cmd == '.':  b = ch == ZTERM
            elif cmd == 'l':
                cpos += 1
                cmd = prog[cpos]
                if cmd == ZTERM: break                       # end of prog
                b = ch == cmd                                # literal character
            else: break                                      # invalid char class

            if tester == '?':
                #  ? => match ok, mismatch fail
                if not b: break  # mismatch fail
            else:
                #  ! => mismatch ok, match fail
                if b: break  # match fail

        elif cmd == '=':
            # REWRITE CHAR
            if data[dpos] == ZTERM: break  # end of data
            cpos += 1
            cmd = prog[cpos]     # char to rewrite as
            if cmd == ZTERM: break   # end of prog
            data[dpos] = cmd

        elif cmd == 'x':
            # EXIT WHOLE PROGRAM
            exiting = True
            break

        elif cmd == '{':
            # ENTER NEW NEST
            cpos += 1  # skip
            dpos = editi(data, dpos, dlen, prog[cpos:])
            if exiting: break  # implements 'x' command

            # recalculate dlen, in case of 'i' or 'd' modifiers
            # If this is a very long string, starting from dpos is quicker
            dlen = dpos + (data.index(ZTERM, dpos) - dpos)

            #  forward scan for matching close '}' in prog
            nests = 1  # count of open nests
            while True:
                if prog[cpos] == ZTERM:
                    cpos -= 1
                    break  # end of prog
                if prog[cpos] == '}':
                    nests -= 1
                    if nests == 0: break  #  matching brace
                elif prog[cpos] == '{':  nests += 1
                cpos += 1

        elif cmd == '*':
            #  LOOP BY REP
            if loops == 255:  # disabled
                #  only write to it the first time we see it
                loops = rep
                loop_start = cpos+1
            rep = 0

        #  non handled commands are just silently ignored

        #  HANDLE REPEATS
        if rep != 0: rep -= 1
        if rep == 0: cpos += 1

    return dpos  # current cursor position


#===== TEST HARNESS ============================================================

#-------------------------------------------------------------------------------
def interactive(debug:bool=False):
    """Prompt for a program and then read and process data"""

    while True:
        # GET PROGRAM
        try:
            prog = input("prog> ")
            if prog == "": break
        except EOFError: break
        except KeyboardInterrupt:
            print()
            break

        while True:
            # GET DATA
            try:
                data = input("data> ")
                if data == "": break
            except EOFError: break
            except KeyboardInterrupt:
                print()
                break

            data, pos = edit(data, prog, debug=debug)
            point(data, pos)
    print("finished!")


#-------------------------------------------------------------------------------
def cli(prog):
    """A driver program to use as a CLI tool"""

    # program is on the command line, but needs to be joined into a single
    # string (and probably externally quoted if any shell globbing used).
    # Data comes from stdin repeatedly as lines, until EOF.
    # each line in the data is processed by the prog and then displayed.

    ##print("# prog:%s" % prog)
    while True:
        try:
            data = sys.stdin.readline()
            if data == "": break  # end of input
        except KeyboardInterrupt:
            print()
            break  # end of program

        # strip newlines
        while len(data) > 0 and data[-1] in ("\r\n"):
            data = data[:-1]

        if data != "":
            # EDIT
            data, pos = edit(data, prog)

            # PRINT
            ##print("pos:", pos)
            print(data[pos:])
        else:
            print()

#----- EXAMPLES ----------------------------------------------------------------
def examples():
    print("""
e                   # skip to end
>>b                 # skip to beginning
>>                  # skip first 2 chars
3>                  # skip first 3 chars
>><                 # left shift
*?s>                # skip whitespace at start
e*?s<               # skip whitespace at end
*?d>                # skip digits at start
*?w>                # skip first word
*?i>                # skip first identifier
*!l.>               # skip to first dot
*!d>                # skip to first number
e*!d<               # skip to end of last number
{*?lA>}{*?lB>}      # skip starting run of A's then B's
{*^>}b              # upper case all
{*v>}b              # lower case all
{*~>}b              # toggle case all
4ib                 # insert 4 spaces at start
8d                  # delete first 8 chars
*?sd                # delete left hand whitespace
e{*?sd<}b           # delete right hand whitespace
{*{*?td}>}b         # delete tabs
{*!l(d}e{*!l)d<}b   # delete start and end fluff and leave brackets
{*!t>}{*?td4i4>}b   # change tabs to 4 spaces
{*{*?lx=.>}>}b      # change 'x' to '.'
    """)

# OTHER EXAMPLES

# hello world
#{*d}i=h>i=e>i=l>i=l>i=o>i= >i=w>i=o>i=r>i=l>i=db

# find first upper case letter
"""*!A>"""

# title case
"""{*{*!w>}^>{*?w>}}"""

# change occurences of "a " to "a big"
# NOTE the >< at the end to force exit when end of string
"""*{{*!la>}>?s>i=b>i=i>i=g>i= >}><"""

# second word to upper case
"""{*?w>}{*!w>}{*?w^>}"""

#----- HELP --------------------------------------------------------------------
def commands():
    print("""
b       move to beginning
e       move to end
>       move right (by repeat)
<       move left (by repeat)

^       upper case
v       lower case
~       toggle case
=       rewrite (as next char)
i       insert to right (by rep)
d       delete to right (by rep)

?       test charset  (match ok, mismatch fail)
!       test charset  (mismatch ok, match fail)

0..9    set repeat count
*       loop sub-program by rep, or until fail
{       enter new sub-program
}       exit this sub-program
x       exit the whole program
    """)

def charsets():
    print("""
d digits (0..9)
s whitespace (space, tab)
w word (upper or lower case letters)
n newline (return or newline)
t tab
l literal char follows
i id (letters digits numbers underscore)
A upper case letters
a lower case letters
y symbol (not alpha, number,digit or ws)
p punctuation (!?.,;:'"`)
. end of data
    """)

def help():
    print("""
stredit - a mini-language that edits strings.

KEY CONCEPTS
It has two 'tapes' - a data tape that holds the string to be edited, 
and a program tape that holds the instructions.

The program is interpreted, one character at a time. 
Each character in the program is a command, and there are many commands.

The data tape holds your string to be edited, 
and it has the concept of a cursor that points to the current character.

Each instruction is a single character that represents a command 
and a command is performed on the character at the cursor.

There are four types of commands:

1. moves the cursor
2. changes the character at the cursor position
3. inspects the character at the cursor position
4. modifies how the program is running.    

For more help try:
commands()
examples()
charsets()

To run a program, use:
run()

To debug a program and generate a trace table, use:
run(debug=True)
""")

#-------------------------------------------------------------------------------
def run(data:str or None=None, prog:str or None=None, debug:bool=False):
    if data is None and prog is None:
        interactive(debug=debug)
        return

    print("running program: %s" % prog)
    print("input data: %s" % data)
    data, pos = edit(data, prog, debug=debug)

    print("results:")
    point(data, pos)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        interactive()
    else:
        cli("".join(sys.argv[1:]))

#END: stredit.py
