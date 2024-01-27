# coding=utf-8

from origin.actions.Actions import Actions
from origin.common.errors.ParseError import ParseError
from origin.common.errors.ActionRefused import ActionRefused


#
# Combine two items in the player's inventory
#
class Combine(Actions):

    @staticmethod
    @Actions.action("combine", "attach", "apply")
    def func(player, parsed, ctx):

        if len(parsed.obj_info) != 2:
            messages = {
                "combine": "Combine which two items?",
                "attach": "Attach which two items?",
                "apply": "Apply which two items?"
            }
            raise ParseError(messages[parsed.verb])

        item1, item2 = tuple(parsed.obj_info)

        if item1 not in player or item2 not in player:
            raise ActionRefused("You do not have both items in your possession.")

        try:
            item2.combine(item1, player)
        except ActionRefused:
            item1.combine(item2, player)