# coding=utf-8

from origin.common.errors.ParseError import ParseError

from origin.actions.Actions import Actions
from origin.parser import Lang
from origin.objects.creatures.Creature import Creature


#
# Express affection or kindness physically
#
class Pet(Actions):

    @staticmethod
    @Actions.action("pet", "stroke", "tickle", "cuddle", "hug")
    def func(player, parsed, ctx):

        if len(parsed.obj_order) != 1:
            raise ParseError("Who would you like to show affection or kindness to?")

        if len(parsed.obj_order) == 1:

            target = parsed.obj_order[0]
            if isinstance(target, Creature):
                player.tell("You %s <creature>%s</creature>." % (parsed.verb, target.title))
                room_msg = "%s %ss %s." % (Lang.capital(player.title), parsed.verb, target.title)
                target_msg = "%s %ss you." % (Lang.capital(player.title), parsed.verb)
                player.location.tell(room_msg, exclude_creature=player, specific_target_msg=target_msg,specific_targets=[target])
            else:
                player.tell("Inanimate objects don't respond to that but it's very sweet of you.")