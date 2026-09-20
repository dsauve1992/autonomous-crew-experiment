"""The rules of the language a report may offer, and the limits they state.

Every `help` line Vine prints comes from here. A help is a rule of the
language rather than a fact about the program -- see **Errors** in
`docs/spec.md` -- so the set of them is finite, and the roster in that section
names the same eighteen strings this module does.

They are in one file for the reason tick 24 found the hard way. The float
ceiling used to be written at the three sites that happened to need it, in two
different sentences, and the four other messages that told a reader something
was too large to be a float said nothing about how large -- not because anyone
decided they should not, but because a rule written at a raise site is found
only by whoever is already standing at that raise site. Two more rules were
duplicated the same way when this module was written: the brace rule was in
`lexer.py` and `parser.py`, and so was the exponent rule, each spelled twice
and equal by coincidence.

Adding a rule here is not the same as offering it. A rule nothing prints and a
message that needs one and has none are both failures, and
`tests/properties/help_roster.py` is what tells them apart.
"""

# -- numbers --------------------------------------------------------------

FLOAT_CEILING = "the largest float is about 1.8e308"

# Vine has no infinities, so "1e400" is not a float the way it is in Python;
# the ceiling alone would leave a reader wondering what the value became.
FINITE_RULE = f"every float is finite; {FLOAT_CEILING}"

NUMBER_RULE = (
    "the digits are 0 to 9, optionally signed, "
    "with spaces, tabs or newlines around them"
)

# The most digits `fixed` will write after the point. 1074 is not a round
# number and is not meant to be: the smallest float Vine has is 5e-324, which
# is exactly 2 ** -1074, and its decimal expansion ends at the 1074th place.
# So every float can be written out exactly, and every digit past the ceiling
# would be a zero. A ceiling is needed at all because Python's formatter
# refuses a precision above 2 ** 31 by raising, and below that quietly builds
# a string of that many characters.
MAX_DIGITS = 1074

FIXED_DIGITS_RULE = (
    f"the smallest float is 5e-324, which has {MAX_DIGITS} "
    "decimal places; nothing has more"
)

# Offered only when the caller passed a default and the conversion refused
# anyway, which is the one moment a reader is owed the boundary: they asked
# for a failure to become a value and got a failure.
CONVERT_DEFAULT_RULE = (
    "a default answers for text that is not a number, and for nothing else"
)

EXPONENT_RULE = "there is no exponent operator; x to the power y is pow(x, y)"

# Offered to a line that opens with an infix operator. The same wrapped
# expression is legal inside `(` `)`, where newlines are ignored, and the
# rule is what says why it stopped being legal inside `{` `}`.
CONTINUATION_RULE = (
    "a line ending in an operator continues onto the next; "
    "only '|>' continues from the left"
)

# -- functions ------------------------------------------------------------

RETURN_RULE = (
    "only a function body may return; "
    "a block's value is its last statement"
)

# -- ending ---------------------------------------------------------------

# Offered to a `fail` with nothing after it. The rule is not "an expression
# goes here" -- the grammar says that. It is why this statement has no bare
# form where `return` does: the value is the whole of what the program gets to
# say, and a status of 1 with an empty stderr is the one ending the contract
# in **Errors** forbids outright.
FAIL_RULE = (
    "'fail' ends the program with its message on stderr and a status of 1; "
    "a failure that says nothing cannot be acted on"
)

# Offered wherever an `import` cannot be carried out. Both halves are rules
# rather than facts about this program: the name is a literal because which
# files a program is made of must be readable from the source, and it is
# resolved beside the importing file because a module is a piece of the
# program and the working directory is not.
IMPORT_RULE = (
    "'import' takes a plain string, and finds that file beside the one doing "
    "the importing"
)

# Offered when an import comes back round to a file already being loaded. It
# names the shape rather than the files, because the files are in the notes.
CYCLE_RULE = (
    "a file cannot be part of loading itself; move what both files need into "
    "a third that neither imports"
)

# How deep Vine calls may nest. Here rather than in `interp.py`, where it was
# until tick 36, for this module's reason: the number is now in a rule, and a
# limit spelled in one file and offered from another is the duplication the
# float ceiling taught. `MAX_VALUE_DEPTH` is picked against it -- see below.
MAX_DEPTH = 500

# What the limit is, and the one walk it does not bound. Offered by every
# report of it, because the implementation cannot tell a runaway recursion
# from a correct one that is simply longer than 500, and this rule is the way
# out of both. `map`, `filter` and `reduce` call their function once per
# element and each call returns before the next begins, so a fold over a
# million records is one call deep. See **Bindings** in docs/spec.md.
CALL_DEPTH_RULE = (
    f"a call may nest {MAX_DEPTH} deep; map, filter and reduce "
    "walk a list of any length without nesting"
)

# -- lists and maps -------------------------------------------------------

# How many containers a walk of a value may enter. Every question that reads a
# whole value -- `==`, `repr`, `str`, printing it, offering it as a key --
# descends one container at a time, and this is where it stops.
#
# 1000 is picked against three measurements, not against taste. Every
# hand-written value in this repository is **two** deep; the deepest thing
# `examples/` builds is a list of maps. A literal at the parser's ceiling is
# 200 deep, so the number has to be above that or a program the parser accepts
# could build a value nothing can print. And a value nested once per *call*
# meets `MAX_DEPTH` at 500 first, which is the better message -- so what
# reaches 1000 is a value built by a loop, which is exactly what this limit is
# about. See **Bindings** in docs/spec.md.
MAX_VALUE_DEPTH = 1000

VALUE_DEPTH_RULE = (
    f"a value may nest {MAX_VALUE_DEPTH} deep; building a deeper one "
    "is not an error until something reads it"
)


COUNT_RULE = "a negative index counts from the end, but a count does not"

SET_RULE = "to give a key a new value, use set(m, k, v)"

# What may be a key. Stated as the permission rather than the refusal,
# because the refusal is one type out of eight and the reader who has just
# been refused is holding the other seven.
KEY_RULE = "a key may be any value that holds no function"

# -- input ----------------------------------------------------------------

# Offered when `read()` is asked for input a program was never given. The rule
# is not "you forgot a redirect" -- that is a fact about one command line. It
# is that Vine never names a file: the only input a program has is the one the
# shell hands it, which is what makes `read()` take no argument.
INPUT_RULE = (
    "a program reads the standard input it was given; "
    "redirect a file into it with 'vine prog.vine < file'"
)

# -- strings --------------------------------------------------------------

ESCAPE_RULE = 'the escapes are \\n \\t \\r \\" \\\\ \\{ \\} and \\u{...}'

CODEPOINT_RULE = "a codepoint is written '\\u{1e}' -- hex digits in braces"

SURROGATE_RULE = (
    "'\\u{d800}' to '\\u{dfff}' are reserved and are not text; "
    "a string holding one could not be printed"
)

BRACE_RULE = "a literal brace is written '\\{'"

HOLE_RULE = (
    "a hole holds one expression, with no format after it; "
    'for decimal places write "{fixed(x, 2)}"'
)
