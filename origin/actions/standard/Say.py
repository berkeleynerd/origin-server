# coding=utf-8

from origin.actions.Actions import Actions
from origin.common.errors.ActionRefused import ActionRefused


#
# Talk with other players in your location
# The @no_parser decorator makes the full text available to the method
#
class Say(Actions):

    @staticmethod
    @Actions.action("say")
    @Actions.no_parser
    def func(player, parsed, ctx):

        if not parsed.unparsed:
            raise ActionRefused("What would you like to say? You should use the form <userinput>say [to name] 'your message'</userinput>")

        message = parsed.unparsed

        # Figure out who the player is trying to talk to. Requires the form:
        # 'Say to <creature> well, hello there

        # TODO: We should handle the case of form 'Say message to <creature>'

        target = ""
        if parsed.obj_order:
            possible_target = parsed.obj_order[0]
            if parsed.obj_info[possible_target].previous_word == "to":
                if parsed.args[0] in (possible_target.name, possible_target.title) or parsed.args[0] in possible_target.aliases:
                    target = " to " + possible_target.title
                    _, _, message = message.partition(parsed.args[0])
                    message = message.lstrip()

                # TODO: Remind user that the other creature must be in the room with them
                # e.g., raise ActionRefused("You can't say that%s as they don't appear to be here with you.", target)

        player.tell("You say%s: %s" % (target, message))
        player.tell_others("{Title} says%s: %s" % (target, message))
