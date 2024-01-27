# coding=utf-8

from origin.parser import Lang
from origin.common.errors.ParseError import ParseError

from origin.actions.Actions import Actions
from origin.objects.creatures.Creature import Creature


#
# Find items, players, or NPCs
#
class Locate(Actions):

    @staticmethod
    @Actions.disable_notify
    @Actions.action("locate", "search", "find")
    def func(player, parsed, ctx):

        if not parsed.args:
            raise ParseError("Who or what are you trying to find?")

        if len(parsed.args) > 1 or len(parsed.obj_order) > 1:
            raise ParseError("You can only search for one thing at a time.")

        name = parsed.args[0]
        player.tell("You search your surroundings to try to find %s." % name)
        player.tell_others("{Title} appears to be looking for something or someone.")

        if parsed.obj_order:

            thing = parsed.obj_order[0]

            if thing is player:
                player.tell("You are in the <location>%s</location>." % player.location.name)
                return

            if thing.name.lower() != name.lower() and name.lower() in thing.aliases:
                player.tell("Maybe you meant %s?" % thing.name)

            if thing in player.location:
                if isinstance(thing, Creature):
                    player.tell("<creature>%s</creature> is right here with you." % Lang.capital(thing.title))
                else:
                    Actions.print_object_location(player, thing, player.location, False)
            elif thing in player:
                Actions.print_object_location(player, thing, player, False)
            else:
                player.tell("You can't seem to find that here.")


        # The default parser checks inventory and location, but it didn't find anything.
        # Check inside containers in the player's inventory instead.
        else:

            item, container = player.locate_item(name, include_inventory=False, include_location=False, include_containers=True)

            if item:

                if item.name.lower() != name.lower() and name.lower() in item.aliases:
                    player.tell("Maybe you meant %s?" % item.name)
                Actions.print_object_location(player, item, container, False)

            else:

                otherplayer = ctx.engine.search_player(name)

                if otherplayer:
                    player.tell("You look about but don't see <player>%s</player>. Yelling might help if %s is nearby." %
                                (Lang.capital(otherplayer.title), otherplayer.subjective))
                else:
                    player.tell("You can't seem to find that here.")