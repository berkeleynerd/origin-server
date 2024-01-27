# coding=utf-8

from origin.common.errors.ParseException import ParseException
from origin.parser.ParseResult import ParseResult


#
# We've encountered a verb that the parser proper doesn't understand so
# so we pass the parsed syntax back to the caller so it can try to
# process the verb as a game specific action.
#
class NotDefaultVerb(ParseException):

    def __init__(self, parsed):
        assert isinstance(parsed, ParseResult)
        super(NotDefaultVerb, self).__init__(parsed.verb)
        self.parsed = parsed
