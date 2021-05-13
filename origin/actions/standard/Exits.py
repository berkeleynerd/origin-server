# coding=utf-8

from origin.actions.Actions import Actions


#
# Provides clues about exits from player's current location.
#
class Exits(Actions):

    @staticmethod
    @Actions.action("exits", "exit")
    def func(player, parsed, ctx):

        if player.isSysOp:

            player.tell("The following exits are available:")
            for direction, exit in player.location.exits.items():
                if exit.bound:
                    player.tell(" <exit>%s</exit> leads to <location>%s</location>" % (direction, exit.target.name))
                else:
                    player.tell(
                        " <exit>%s</exit> leads to <location>%s</location> (unbound)" % (direction, exit.target))

        else:

            player.tell("If you look around you'll get some information about possible exits leading to other locations.")
            player.tell("Some exits might be hidden so you'll need to search for them but it's rare.")
