# coding=utf-8

from origin.actions.Actions import Actions
from origin.common.errors.ParseError import ParseError
from origin.common.errors.ActionRefused import ActionRefused
from origin.common.errors.RetryParse import RetryParse


#
# Help the user by understanding the common "where am i" phrase
#
class Where(Actions):

    @staticmethod
    @Actions.disable_notify
    @Actions.action("where")
    def func(player, parsed, ctx):

        if not parsed.args:
            raise ParseError("Who or what are you trying to find?")

        if len(parsed.args) == 2 and parsed.args[0] == "am":
            if parsed.args[1].rstrip("?") in ("i", "I"):
                player.tell("You're in %s." % player.location.title)
                player.tell("If you say <userinput>look</userinput> I'll tell you a bit more about where you are.")
                return

        if parsed.args[0] in ("is", "are") and len(parsed.args) > 2:
            raise ActionRefused("Please be specific and realize that I can only search for one thing at a time.")

        if len(parsed.args) >= 2 and parsed.args[0] in ("is", "are"):
            del parsed.args[0]

        name = parsed.args[0].rstrip("?")
        raise RetryParse("locate " + name)