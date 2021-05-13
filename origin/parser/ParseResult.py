# coding=utf-8

from origin.parser.ObjectInfo import ObjectInfo

#
# Defines the structure into which input text is parsed.
#
class ParseResult(object):


    __slots__ = ("verb", "message", "obj_info", "obj_order", "args", "unrecognized", "unparsed")


    def __init__(self, verb, message=None, args=None, obj_info=None, obj_order=None, unrecognized=None, unparsed=""):

        self.verb = verb
        self.message = message
        self.obj_info = obj_info or {}      # ObjectInfo for all objects parsed. Includes items, creatures, and exits.
        self.obj_order = obj_order or []    # Order of objects in the unparsed text.
        self.args = args or []
        self.unrecognized = unrecognized or []
        self.unparsed = unparsed

        if self.obj_order and not self.obj_info:
            self.obj_info = {}
            for sequence, obj in enumerate(self.obj_order):
                self.obj_info[obj] = ObjectInfo(sequence)


    def __str__(self):

        obj_info_str = [" %s->%s" % (creature.name, info) for creature, info in self.obj_info.items()]

        s = [
            "ParseResult:",
            " verb=%s" % self.verb,
            " message=%s" % self.message,
            " args=%s" % self.args,
            " unrecognized=%s" % self.unrecognized,
            " obj_info=%s" % "\n".join(obj_info_str),
            " obj_order=%s" % self.obj_order,
            " unparsed=%s" % self.unparsed
        ]

        return "\n".join(s)