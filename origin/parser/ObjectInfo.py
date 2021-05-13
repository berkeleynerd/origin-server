# coding=utf-8


class ObjectInfo(object):

    __slots__ = ("sequence", "previous_word")

    def __init__(self, sequence=0):

        self.sequence = sequence
        self.previous_word = None

    def __str__(self):
        return "[sequence=%d, prev_word=%s]" % (self.sequence, self.previous_word)