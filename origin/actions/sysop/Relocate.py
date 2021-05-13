# coding=utf-8

from origin.actions.Actions import Actions
from origin.common.errors.ActionRefused import ActionRefused
from origin.common.errors.ParseError import ParseError
from origin.objects.creatures.Creature import Creature


#
# Move an item or creature to another location. This allows normally immovable objects to be taken or given to
# another creature, etc...
#
# ex: 'relocate [name] here' relocates an item to the player's current location
# ex: 'transport [name] to [name]' transports an item to a creature's inventory
#
class Relocate(Actions):

    @staticmethod
    @Actions.action("relocate")
    @Actions.sysop
    def func(player, parsed, ctx):

        if len(parsed.args) != 2 or len(parsed.obj_order) < 1:
            raise ActionRefused("You must specify what to move and where to move it."
                                "Only functional for items and creatures in your current location.")

        thing = parsed.obj_order[0]
        if isinstance(thing, Creature):
            raise ActionRefused("Use the 'transport' action to move creatures to another location.")

        # Is the player's current location the target?
        if parsed.args[1] == "here" and len(parsed.obj_order) == 1:
            target = player.location

        # If not the target must be another creature's inventory
        elif len(parsed.obj_order) == 2:
            target = parsed.obj_order[1]

        else:
            raise ParseError("I'm not sure what you want to move or where you want to move it to.")

        if thing is target:
            raise ActionRefused("You can not move something inside itself.")

        # What sort of container are we moving the item into?
        if thing in player:
            thing_container = player
        elif thing in player.location:
            thing_container = player.location
        else:
            raise ParseError("I don't understand what you are trying to move the item into.")

        thing.move(target, player)
        player.tell("Successfully moved <item>%s</item> from %s to %s." % (thing.name, thing_container.name, target.name))