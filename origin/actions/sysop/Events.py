# coding=utf-8

from origin.actions.Actions import Actions

#
# Display pending actions.
#
class Events(Actions):

    @staticmethod
    @Actions.action("events")
    @Actions.sysop
    def func(player, parsed, ctx):

        engine = ctx.engine
        config = ctx.config

        player.tell("Pending Events")
        player.tell("################")
        player.tell("Active heartbeats (%d total):" % len(engine.heartbeats))
        player.tell("################")

        for hb in engine.heartbeats:
            player.tell(" " + str(hb))

        num_shown = min(50, len(engine.deferreds))
        player.tell("Showing %d of %d total deferreds with server tick at %.1f sec)" % (num_shown, len(engine.deferreds), config.server_tick_time))

        for d in engine.deferreds:
            player.tell("Due      :", d.when_due(ctx.clock, realtime=True))
            player.tell("Function :", d.action)
            player.tell("Owner    :", d.owner)

        player.tell("################")
