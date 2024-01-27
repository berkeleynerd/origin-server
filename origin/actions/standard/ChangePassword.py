# coding=utf-8

from origin.actions.Actions import Actions
from origin.common.errors.ActionRefused import ActionRefused
from origin.objects.creatures.players.Accounts import Accounts


#
# Allow the user to change their password.
#
class ChangePassword(Actions):

    @staticmethod
    @Actions.action("change_password")
    def func(player, parsed, ctx):

        current_pw = yield "input-noecho", "What is the secret that we share?<password>"
        new_pw = yield "input-noecho", ("What is the new secret we should both know?<password>", Accounts.accept_password)

        try:
            ctx.engine.accounts.change_password(player.name, current_pw, new_password=new_pw)
            player.tell("Keep it secret. Keep it safe.")
        except ValueError as x:
            raise ActionRefused("%s" % x)