"""The rules of the language a report may offer, and the limits they state.

Every `help` line Vine prints comes from here. A help is a rule of the
language rather than a fact about the program -- see **Errors** in
`docs/spec.md` -- so the set of them is finite, and the roster in that section
names the same fifteen strings this module does.

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

# -- lists and maps -------------------------------------------------------

COUNT_RULE = "a negative index counts from the end, but a count does not"

SET_RULE = "to give a key a new value, use set(m, k, v)"

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
