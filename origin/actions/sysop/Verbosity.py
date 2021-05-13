# coding=utf-8

from origin.actions.Actions import Actions
from origin.common.errors.ParseError import ParseError


#
# Sets the verbosity of descriptions for locations already visited.
#
# 'on'    enables short descriptions for all locations
# 'off'   restores full descriptions for all locations
# 'known' enables short descriptions for visited locations
#
class Verbosity(Actions):

    @staticmethod
    @Actions.action("brief")
    @Actions.disable_notify
    @Actions.sysop
    def func(player, parsed, ctx):

            if parsed.unparsed == "off" or (parsed.args and parsed.args[0] == "off"):
                player.brief = 0
                player.tell("Full descriptions restored.")
            elif not parsed.args or parsed.unparsed == "on" or (parsed.args and parsed.args[0] == "on"):
                player.brief = 2
                player.tell("Short descriptions enabled.")
            elif parsed.args[0] == "known":
                player.brief = 1
                player.tell("Short descriptions enabled for all known locations.")
            else:
                raise ParseError("I do not recognize that parameter.")
