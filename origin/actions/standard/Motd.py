# coding=utf-8

from origin.actions.Actions import Actions


#
# Display the Message of the Day
#
class Motd(Actions):

    @staticmethod
    @Actions.action("motd")
    @Actions.disable_notify
    def func(player, parsed, ctx):

        ctx.engine.show_motd(player, notify_no_motd=True)