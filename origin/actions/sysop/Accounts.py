# coding=utf-8

from origin.actions.Actions import Actions

#
# Display all active player accounts
#
class Accounts(Actions):

    @staticmethod
    @Actions.action("accounts")
    @Actions.sysop
    def func(player, parsed, ctx):

        accounts = ctx.engine.accounts.all_accounts()

        for name, account in accounts.items():
            player.tell("name   :", account["name"])
            player.tell("\n")
            player.tell("online :", account["logged_in"])
            player.tell("\n")
            player.tell("email  :", account["email"])
            player.tell("\n")
            player.tell("sysop  :", account["isSysOp"])
