# coding=utf-8

from origin.actions.Actions import Actions
from origin.actions import Examine


#
# Look around to see where you are and what's around you."""
#
class Look(Actions):

    @staticmethod
    @Actions.action("look", "close", "lock", "unlock")
    @Actions.disable_notify
    def func(player, parsed, ctx):

        # Player has specified something in particular to look at
        if parsed.args:

            arg = parsed.args[0]

            # If player is looking a particular direction we can handle that here
            # otherwise we'll turn the command over to examine.
            if arg in player.location.exits:

                exit = player.location.exits[arg]

                # Share the detailed description if there is one...
                if exit.short_description != exit.description and exit.description is not None and exit.description != "":
                    player.tell(exit.description)
                else:
                    player.tell(exit.short_description)
                    return

            # Player just wants to look "around" ... ok
            elif arg == "around":
                player.look(short=False)

            # Not sure what to do so we'll call examine for the player
            else:
                Examine.func(player, parsed, ctx)

        # Player just wants to take a gander at the room around them
        else:
            player.look(short=False)