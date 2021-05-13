# coding=utf-8

from origin.common.errors.ParseError import ParseError

from origin.actions.Actions import Actions
from origin.parser import Lang
from origin.objects.creatures.players import Player


#
# Remove all items within a container, creature's inventory, or the present location.
#
class Clean(Actions):

    @staticmethod
    @Actions.action("clean")
    @Actions.sysop
    def func(player, parsed, ctx):

        # Remove all objects from the player's current location
        if parsed.args and parsed.args[0] == '.':

            player.tell("Removing all non-player objects from your current location.")

            for item in set(player.location.items):
                player.location.remove(item, player)
                item.destroy(ctx)

            for creature in set(player.location.creatures):
                if not isinstance(creature, Player.Player):
                    player.location.remove(creature, player)
                    creature.destroy(ctx)

            if player.location.items:
                player.tell("Some items were unable to be removed.")

        else:

            if len(parsed.obj_order) != 1:
                raise ParseError("Please specify the container or creature you are trying to remove all objects from.")

            target = parsed.obj_order[0]
            if (yield "input", ("Are you sure you want to remove all items from %s?" % target.title, Lang.yesno)):

                player.tell("Removing all items from %s." % target)

                items = target.inventory
                for item in items:
                    target.remove(item, player)
                    item.destroy(ctx)
                    player.tell(item, "removed from the world.")

                if target.inventory_size:
                    player.tell("Some items were unable to be removed.")

            else:

                player.tell("Action cancelled.")