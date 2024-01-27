# coding=utf-8

from origin.common.errors.ParseException import ParseException


#
# We've encountered a verb that the parser proper and the game engine both
# do not understand. We'll need to let the player know we can't make sense
# of their message and let them try again.
#
class UnknownVerbException(ParseException):

    def __init__(self, verb, words):
        super(UnknownVerbException, self).__init__(verb)
        self.verb = verb
        self.words = words
