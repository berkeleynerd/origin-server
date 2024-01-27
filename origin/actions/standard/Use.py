# coding=utf-8

from origin.actions.Actions import Actions
from origin.common.errors.ActionRefused import ActionRefused
from origin.objects.creatures.Creature import Creature


#
# Use an item. Often the player will have to be specific and specify exactly what to do with it.
#
class Use(Actions):

    @staticmethod
    @Actions.action("use")
    def func(player, parsed, ctx):

        if not parsed.obj_order:
            raise ActionRefused("What do you want to use?")

        subj = ""

        if len(parsed.obj_order) > 1:

            item1, item2 = tuple(parsed.obj_info)
            if item1 in player and item2 in player:
                ActionRefused("To use multiple items together you'll need to combine them first.")

        else:

            who = parsed.obj_order[0]
            if isinstance(who, Creature):
                if who is player:
                    raise ActionRefused("You can't use another player.")
                subj = who.objective
            else:
                subj = "it"

        raise ActionRefused("You'll need to be more specific and tell me exactly what you want to do with %s." % subj)