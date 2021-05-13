# coding=utf-8

from origin.actions.Actions import Actions
from origin.common.errors.ParseError import ParseError
from origin.common.errors.ActionRefused import ActionRefused


#
# Deactivate an item
#
class Deactivate(Actions):

    @staticmethod
    @Actions.action("deactivate")
    def func(player, parsed, ctx):

        if not parsed.obj_order:
            raise ParseError("What are you trying to deactivate?")

        for what in parsed.obj_order:
            try:
                what.deactivate(player)
            except ActionRefused as ex:
                msg = str(ex)
                if len(parsed.obj_order) > 1:
                    player.tell("%s: %s" % (what.name, msg))
                else:
                    player.tell(msg)