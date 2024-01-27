# coding=utf-8

import inspect

from origin.actions.Actions import Actions
from origin.common.errors.ActionRefused import ActionRefused
from origin.common.errors.ParseError import ParseError


#
# Displays the python object attribute values of a location, item, or creature.
#
class Dump(Actions):

    @staticmethod
    @Actions.action("dump")
    @Actions.sysop
    def func(player, parsed, ctx):

        if not parsed.args:
            raise ParseError("Display the internal attributes associated with what location, item, or creature?")

        name = parsed.args[0]
        if name == "location":
            obj = player.location
        elif parsed.obj_order:
            obj = parsed.obj_order[0]
        else:
            raise ActionRefused("I can't locate the object %s." % name)

        player.tell(["%r" % obj, "Python class defined in module : " + inspect.getfile(obj.__class__)])

        for varname, value in sorted(vars(obj).items()):
            player.tell(".%s: %r" % (varname, value))

        if obj in ctx.engine.heartbeats:
            player.tell("%s is subscribed to heartbeat topic." % obj.name)
