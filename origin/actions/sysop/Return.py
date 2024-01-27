# coding=utf-8

from origin.actions.Actions import Actions
from origin.common.errors.ActionRefused import ActionRefused


#
# Return a creature to the location they were transported from
#
class Return(Actions):

    @staticmethod
    @Actions.action("return")
    @Actions.sysop
    def func(player, parsed, ctx):

            if len(parsed.obj_order) == 1:
                who = parsed.obj_order[0]
            elif len(parsed.obj_order) == 0:
                who = player
            else:
                raise ActionRefused("Only one creature can be returned at a time.")

            previous_location = getattr(who, "transported_from", None)
            if previous_location:
                del who.transported_from
                who.move(previous_location, silent=False)
            else:
                player.tell("I can not determine the creature's previous location.")