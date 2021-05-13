# coding=utf-8

from origin.common.errors.ParseError import ParseError

from origin.actions.Actions import Actions
from origin.parser import Lang


#
# Express an emotion in the form "express seems perplexed"
# This yields the output "{player_name} seems perplexed"
#
class Emote(Actions):

    @staticmethod
    @Actions.action("express", "emote")
    def func(player, parsed, ctx):

        if not parsed.unparsed:
            raise ParseError("What feeling are you trying to express?")

        message = Lang.capital(player.title) + " " + parsed.unparsed
        player.tell("%s" % message)
        player.tell_others(message)