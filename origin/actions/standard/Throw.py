# coding=utf-8

from origin.actions.Actions import Actions
from origin.common.errors.ParseError import ParseError
from origin.common.errors.ActionRefused import ActionRefused
from origin.objects.creatures.Creature import Creature


#
#  Toss something in inventory at someone or something. Will automatically pick up the item if not in inventory.
#
class Throw(Actions):

    @staticmethod
    @Actions.action("throw", "toss")
    def func(player, parsed, ctx):

            if len(parsed.obj_order) != 2:
                raise ParseError("You need to tell me what to throw and where to throw it.")

            item, where = parsed.obj_order[0], parsed.obj_order[1]

            if isinstance(item, Creature):
                raise ActionRefused("You can't throw another living creature.")

            # If the item is in the room with the player we'll need to pick it up first
            if item in player.location:

                item.move(player, player, verb="take")
                player.tell("You take <item>%s</item>." % item.title)
                player.tell_others("{Title} takes %s." % item.title)

            # Toss the item at the target.
            item.move(player.location, player, verb="throw")

            player.tell("You throw the <item>%s</item> at %s" % (item.title, where.title))
            player.tell_others("{Title} throws the %s at %s." % (item.title, where.title))
