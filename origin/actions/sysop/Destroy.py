# coding=utf-8

from origin.common.errors.ParseError import ParseError

from origin.actions.Actions import Actions
from origin.parser import Lang


#
# Remove an object from the world
#
class Destroy(Actions):

    @staticmethod
    @Actions.action("destroy")
    @Actions.sysop
    def func(player, parsed, ctx):

        if not parsed.obj_order:
            raise ParseError("Which object are we removing from the world?")

        if parsed.unrecognized:
            raise ParseError("I could not parse that into an in-world object")

        for target in parsed.obj_info:

            if not (yield "input", ("Are you sure you want to remove %s from the world?" % target.title, Lang.yesno)):
                player.tell("Action cancelled.")
                continue

            target.sys_destroy(player, ctx)
            player.tell("You remove %r from the world." % target)