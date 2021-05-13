# coding=utf-8

from origin.actions.Actions import Actions
from origin.common.errors.ParseError import ParseError


#
# Read an item's text
#
class Read(Actions):

    @staticmethod
    @Actions.action("read")
    def func(player, parsed, ctx):

        if len(parsed.obj_order) == 1:
            what = parsed.obj_order[0]
            what.read(player)
        else:
            raise ParseError("What would you like to read?")
