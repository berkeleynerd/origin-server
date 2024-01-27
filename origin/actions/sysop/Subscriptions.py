# coding=utf-8

from origin.actions.Actions import Actions
from origin.engine.pubsub.Topic import Topic

#
# Display information about subscription topics
#
class Subscriptions(Actions):

    @staticmethod
    @Actions.action("subscriptions")
    @Actions.sysop
    def func(player, parsed, ctx):

        pending = Topic.pending()
        player.tell("Pending Messages")
        player.tell("################")
        player.tell("Active topics (%d total) :" % len(pending))
        player.tell("################")
        total = 0

        for topic in sorted(pending, key=lambda t: str(t)):
            iPending, idle, subscribers = pending[topic]
            total += iPending
            if iPending or subscribers or idle < 10:
                player.tell("topic       :", topic)
                player.tell("pending     :", pending)
                player.tell("idle        :", int(idle))
                player.tell("subscribers :", subscribers)

        player.tell("################")
        player.tell(("total pending:  " + str(total)))
