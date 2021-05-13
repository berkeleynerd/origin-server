# coding=utf-8

from origin.actions.Actions import Actions
from origin.common.errors.ParseError import ParseError
from origin.common.errors.ActionRefused import ActionRefused
from origin.objects.items.containers.Container import Container


#
# Remove contents of a creature or container
#
class Empty(Actions):

    @staticmethod
    @Actions.action("empty")
    def func(player, parsed, ctx):

        if len(parsed.args) == 0:
            raise ParseError("What would you like to empty?")

        if len(parsed.args) != 1 or not parsed.obj_order:
            raise ParseError("What would you like to empty?")

        # We can't empty more than one container at a time
        if len(parsed.obj_order) > 1:
            raise ParseError("You can only empty one item at a time.")

        # If the object specified isn't a container we can't empty it
        container = parsed.obj_order[0]
        if not isinstance(container, Container):
            raise ActionRefused("That doesn't seem to be something you can empty.")

        # If the sprcified container is in the room we'll empty the contents
        if container in player.location:
            target = player.location
            action = "dropped"
        # Otherwise we'll look for the specified container on the player's person
        elif container in player:
            target = player
            action = "took"
        else:
            raise ParseError("That doesn't seem to be something you can empty.")

        # Try to actually move the items into the player's inventory and let them
        # know if rules for a particular item prevent the action
        items_moved = []
        for item in container.inventory:
            try:
                item.move(target, player)
                items_moved.append(item.title)
            except ActionRefused as x:
                player.tell(str(x))

        if items_moved:
            itemnames = ", ".join(items_moved)
            player.tell("You %s the following items: <item>%s</item>" % (action, itemnames))
            player.tell_others("{Title} %s the following items: <item>%s</item>" % (action, itemnames))
        else:
            player.tell("You %s nothing." % action)