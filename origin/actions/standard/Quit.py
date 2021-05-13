# coding=utf-8

from origin.parser import Lang

from origin.actions.Actions import Actions
from origin.common.errors.SessionExit import SessionExit


#
# Leave the game
#
class Quit(Actions):

    @staticmethod
    @Actions.action("quit")
    @Actions.disable_notify
    def func(player, parsed, ctx):

        if (yield "input", ("Are you sure you want to quit?", Lang.yesno)):
            player.tell("\n")
            raise SessionExit()
