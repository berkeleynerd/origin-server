# coding=utf-8

import datetime
import gc
import platform
import sys

from origin import __version__
from origin.actions.Actions import Actions


#
# Display information about the running server.
#
class Server(Actions):

    @staticmethod
    @Actions.action("server")
    @Actions.sysop
    def func(player, parsed, ctx):

        engine = ctx.engine
        config = ctx.config
        player.tell("Server Information")
        player.tell("################")

        # Gather the various bits
        up_hours, up_minutes, up_seconds = engine.uptime
        realtime = datetime.datetime.now()
        realtime = realtime.replace(microsecond=0)
        pyversion = "%d.%d.%d" % sys.version_info[:3]
        sixtyfour = "(%d bits)" % (sys.maxsize.bit_length() + 1)
        implementation = platform.python_implementation()
        gc_objects = "??" if sys.platform == "cli" else str(len(gc.get_objects()))
        avg_loop_duration = sum(engine.server_loop_durations) / len(engine.server_loop_durations)

        # Display them to the player
        player.tell("Python version  : %s %s %s on %s" % (implementation, pyversion, sixtyfour, sys.platform))
        player.tell("Library version : %s" % __version__)
        player.tell("Game version    : %s %s" % (config.name, config.version))
        player.tell("Uptime          : %d:%02d:%02d since %s" % (up_hours, up_minutes, up_seconds, engine.server_started))
        player.tell("Real time       : %s" % realtime)
        player.tell("Game time       : %s (%dx real time)" % (ctx.clock, ctx.clock.multiplier))
        player.tell("Python objects  : %s" % gc_objects)
        player.tell("Players         : %d" % len(ctx.engine.all_players))
        player.tell("Heartbeats      : %d" % len(engine.heartbeats))
        player.tell("Deferreds       : %d" % len(engine.deferreds))
        player.tell("Loop tick       : %.1f sec" % config.server_tick_time)
        player.tell("Loop duration   : %.2f sec average" % avg_loop_duration)
