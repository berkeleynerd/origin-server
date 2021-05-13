# coding=utf-8

from origin.parser import Lang

from origin.actions import Examine
from origin.actions.Actions import Actions
from origin.common.errors.RetryParse import RetryParse
from origin.common.errors.ActionRefused import ActionRefused


#
# Search for all players, a specific player or creature, and shows some information about them
#
class Who(Actions):

    @staticmethod
    @Actions.action("who", "finger", "whois")
    @Actions.disable_notify
    @Actions.sysop
    def func(player, parsed, ctx):

        # Player wants to examine themselves apparently
        if parsed.args == ["am", "i"]:
            raise RetryParse("examine myself")

        if parsed.args:
            Actions.parse_is_are(parsed.args)
            name = parsed.args[0].rstrip("?")

            # Perform a global search and work from there
            otherplayer = ctx.engine.search_player(name)

            found = False
            if otherplayer:
                found = True

                # Looks like we found them
                player.tell("<player>%s</player> is active and currently at '<location>%s</location>'." % (
                    Lang.capital(otherplayer.title), otherplayer.location.name))

            # Let's see if we can get any additional information about them...
            try:
                Examine.func(player, parsed, ctx)
            except ActionRefused:
                pass

            if not found:
                player.tell("That player does not appear to be online.")

        # The player didn't specify a particular player so list them all
        else:
            player.tell("All players currently in the game:")
            player.tell("\n")
            for conn in ctx.engine.all_players.values():
                other = conn.player
                player.tell("<player>%s</player> (%s) is currently at <location>%s</location>" % (
                    Lang.capital(other.name), other.title, other.location.name))