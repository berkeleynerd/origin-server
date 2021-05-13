# coding=utf-8

from origin.actions.Actions import Actions
from origin.common.errors.ParseError import ParseError
from origin.common.errors.ActionRefused import ActionRefused


#
# Activate an item
#
class Activate(Actions):

    @staticmethod
    @Actions.action("activate")
    def func(player, parsed, ctx):

        if not parsed.obj_order:
            raise ParseError("What are you trying to activate?")

        for what in parsed.obj_order:
            try:
                what.activate(player)
            except ActionRefused as ex:
                message = str(ex)
                if len(parsed.obj_order) > 1:
                    player.tell("%s: %s" % (what.name, message))
                else:
                    player.tell(message)