# coding=utf-8

import collections
import re


#
# Various linguistic maps and constants
#

SUBJECTIVE = {"m": "he", "f": "she", "n": "it"}
POSSESSIVE = {"m": "his", "f": "her", "n": "its"}
OBJECTIVE = {"m": "him", "f": "her", "n": "it"}
GENDERS = {"m": "male", "f": "female", "n": "neuter"}

__a_exceptions = {
    "universe": "a",
    "university": "a",
    "user": "a",
    "hour": "an"
}

__articles = {"the", "a", "an"}

__number_words = [
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty"
]

__tens_words = [
    None, None, "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"
]

__plural_irregularities = {
    "mouse": "mice",
    "child": "children",
    "person": "people",
    "man": "men",
    "woman": "women",
    "foot": "feet",
    "goose": "geese",
    "tooth": "teeth",
    "aircraft": "aircraft",
    "fish": "fish",
    "headquarters": "headquarters",
    "sheep": "sheep",
    "species": "species",
    "cattle": "cattle",
    "scissors": "scissors",
    "trousers": "trousers",
    "pants": "pants",
    "tweezers": "tweezers",
    "congratulations": "congratulations",
    "pyjamas": "pyjamas",
    "photo": "photos",
    "piano": "pianos"
}


# Simple data structure used by join function
class OrderedCounter(collections.Counter, collections.OrderedDict):
    pass


#
# Handles grammar when joining a list of words to produce the form 'one, two, three, and four'
# When group=True words occuring multiple times produce the form 'two things' rather than 'thing and thing'
#
def join(words, conj="and", group=True):


    # e.g., "key, key, key" would become "three keys"
    def apply_amount(count, word):

        prefix, _, rest = word.partition(' ')

        # Remove article when parsing multiple instances of a word.
        if rest and prefix in __articles:
            word = rest

        return spell_number(count) + " " + pluralize(word)


    if not words:
        return ""

    words = list(words)

    if len(words) == 1:
        return words[0]

    # If all words are the same and grouping is desired
    if group and len(set(words)) == 1:
        return apply_amount(len(words), words[0])

    if len(words) == 2:
        return "%s %s %s" % (words[0], conj, words[1])

    if group:

        counts = OrderedCounter(words)
        words = []

        for word, count in counts.items():

            if count == 1:
                words.append(word)
            else:
                words.append(apply_amount(count, word))

        return join(words, conj, group=False)

    return "%s, %s %s" % (", ".join(words[:-1]), conj, words[-1])


#
# A simple function to determine whether to use "a" or "an"
# If the word begins with a vowel return "an", otherwise return "a"
# Does not handle all edge cases.
#
def a(word):

    if not word:
        return ""
    if word.startswith(("a ", "an ")):
        return word
    firstword = word.split(None, 1)[0]
    exception = __a_exceptions.get(firstword.lower(), None)
    if exception:
        return exception + " " + word
    elif word.startswith(('a', 'e', 'i', 'o', 'u')):
        return "an " + word
    return "a " + word


#
# Try to determine the correct possessive form
#
def possessive_letter(name):

    if not name:
        return ""

    # case: Jess' bag
    if name[-1] == 's':
        return "'"

    # case: "Your own"
    elif name.endswith(" own"):
        return ""

    # default:
    else:
        return "'s"


def possessive(name):
    return name + possessive_letter(name)


#
# Similar to string.capitalize but does not force lowercase on the rest of the string
#
def capital(string):

    if string:
        string = string[0].upper() + string[1:]

    return string


#
# Changes verb to progressive tense.
# e.g., look becomes looking, etc...
#
def progressive_tense(verb):

    if verb[-1] == "e":
        return verb[:-1] + "ing"
    return verb + "ing"


#
# Splits a string on whitespace but skips words enclosed in quotes. Quotes are removed.
#
def split(string):

    def removequotes(word):

        if word.startswith(('"', "'")) and word.endswith(('"', "'")):
            return word[1:-1].strip()

        return word

    return [removequotes(p) for p in re.split("( |\\\".*?\\\"|'.*?')", string) if p.strip()]


#
# Return the proper word associated with a number. Supports positive and negative integers, floating point values,
# and common fractional values such as 0.5 and 0.25. A number n that are very near a whole number are
# returned as "about n". Fractions that can not be properly phrased will be returned as simple numbers.
#
def spell_number(number):


    def spell_positive_int(n):

        if n <= 20:
            return __number_words[n]

        tens, ones = divmod(n, 10)

        if tens <= 9:
            if ones > 0:
                return __tens_words[tens] + " " + __number_words[ones]
            return __tens_words[tens]

        return str(n)


    sign = ""
    orig_number = number
    if number < 0:
        sign = "minus "
        number = -number

    whole, fraction = divmod(number, 1)
    whole = int(whole)

    if fraction == 0.0:
        return sign + spell_positive_int(whole)

    elif fraction == 0.5:
        return sign + spell_positive_int(whole) + " and a half"

    elif fraction == 0.25:
        return sign + spell_positive_int(whole) + " and a quarter"

    elif fraction == 0.75:
        return sign + spell_positive_int(whole) + " and three quarters"

    elif fraction > 0.995:
        return "about " + sign + spell_positive_int(whole + 1)

    elif fraction < 0.005:
        return "about " + sign + spell_positive_int(whole)

    # We can't deal with any additional cases so the original value will just have to do
    return str(orig_number)


#
# Pluralize words in all their linguistic forms. Or at least, as many as we can tolerate accomodating.
#
def pluralize(word, amount=2):

    if amount == 1:
        return word

    if word in __plural_irregularities:
        return __plural_irregularities[word]

    if word.endswith("is"):
        return word[:-2] + "es"

    if word.endswith("z"):
        return word + "zes"

    if word.endswith("s") or word.endswith("ch") or word.endswith("x") or word.endswith("sh"):
        return word + "es"

    if word.endswith("y"):

        if len(word) > 1 and word[-2] in "aeio":
            return word + "s"

        return word[:-1] + "ies"

    if word.endswith("f"):
        return word[:-1] + "ves"

    if word.endswith("fe"):
        return word[:-2] + "ves"

    if word.endswith("o") and len(word) > 1 and word[-2] not in "aeiouy":
        return word + "es"

    return word + "s"


#
# Understand many variations of "yes" and "no"
#
def yesno(value):

    value = value.lower() if value else ""

    if value in {"y", "yes", "sure", "yep", "yeah", "yessir", "sure thing"}:
        return True

    if value in {"n", "no", "nope", "no way", "hell no"}:
        return False

    raise ValueError("That does not apear to be a valid yes or no response.")


#
# Basically, if it begins with the first character from the list of supported genders we'll take it
#
def validate_gender(value):

    value = value.lower() if value else ""

    if value in GENDERS:
        return value

    if len(value) > 1:
        if value[0] in GENDERS and GENDERS[value[0]] == value:
            return value

    raise ValueError("That does not apear to be a valid gender.")
