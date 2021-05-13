# coding=utf-8

from origin.actions.Actions import Actions
from origin.common.errors.ActionRefused import ActionRefused


#
# Allow Sysop to send a private message to a player or creature anywhere in the world
#
class Tell(Actions):

    @staticmethod
    @Actions.action("tell")
    @Actions.sysop
    def func(player, parsed, ctx):

        if len(parsed.args) < 1:
            raise ActionRefused("Who are you trying to communicate with? You should use the form <userinput>tell [to name] 'your message'</userinput>")

        name = parsed.args[0]
        creature = player.location.search_creature(name)
        if not creature:
            creature = ctx.engine.search_player(name)  # is there a player around with this name?
            if not creature:
                raise ActionRefused("%s is not online." % name)

        # We found the person or creature. Make sure it isn't the player his/herself
        if creature is player:
            player.tell("A voice booms from deep within your mind 'Talk to yourself on your own time!'")
        # Seems to be a legit target
        else:
            # Some text formatting stuff
            # TODO: See Say.py for some limitations we should correct here too
            if parsed.unparsed[0:3] == "to " and len(parsed.unparsed.strip()) > 5:
                unparsed = parsed.unparsed[len(name) + 3:].lstrip()
            else:
                unparsed = parsed.unparsed[len(name):].lstrip()

            if unparsed:
                creature.tell("<player>%s</player> tells you: %s" % (player.name, unparsed))
                player.tell("You sent <creature>%s</creature> the message: %s" % (name, unparsed))
            # Looks like they forgot to provide a message.
            else:
                player.tell("What would you like to tell %s?" % creature.objective)