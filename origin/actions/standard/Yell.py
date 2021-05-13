# coding=utf-8

from origin.actions.Actions import Actions
from origin.common.errors.ActionRefused import ActionRefused


#
# Allows the player to yell something and have it heard by anyone in an adjacent location
#
class Yell(Actions):

    @staticmethod
    @Actions.action("yell", "scream", "shout", "holler")
    def func(player, parsed, ctx):

        if not parsed.unparsed:
            raise ActionRefused("What do you wish to shout at the top of your lungs?")

        message = parsed.unparsed
        if not parsed.unparsed.endswith((".", "!", "?")):
            message += "!"

        player.tell("You scream '%s'" % message)
        player.tell_others("{Title} shouts '%s'" % message)
        player.location.tell_adjacent_locations("Someone nearby shouts '%s'" % message)