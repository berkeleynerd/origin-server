# coding=utf-8

import datetime

from origin.actions.Actions import Actions
from origin.common.errors.ActionRefused import ActionRefused
from origin.objects.items.standard.Clock import Clock


#
# Give the player (or Sysop) the time. The former only if they have a timepiece, however.
#
class Time(Actions):

    @staticmethod
    @Actions.action("time", "date")
    @Actions.disable_notify
    def func(player, parsed, ctx):

        if player.isSysOp:
            real_time = datetime.datetime.now()
            real_time = real_time.replace(microsecond=0)
            player.tell("In-game time is currently", ctx.clock)
            player.tell("Server time reports", real_time)
            return

        for item in player.inventory:
            if isinstance(item, Clock):
                player.tell("You glance at your %s." % item.name)
                player.tell(item.description)
                return

        raise ActionRefused("You don't have a watch or see a clock anywhere so you're unsure what %s it is." % parsed.verb)