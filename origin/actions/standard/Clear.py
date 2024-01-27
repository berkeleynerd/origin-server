# coding=utf-8

from origin.actions.Actions import Actions


#
# The good old cls command
#
class Clear(Actions):

    @staticmethod
    @Actions.action("cls", "clear")
    @Actions.disable_notify
    def func(player, parsed, ctx):
        ctx.conn.clear_screen()
