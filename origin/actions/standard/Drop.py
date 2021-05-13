# coding=utf-8

from origin.parser import Lang
from origin.common.errors.ParseError import ParseError
from origin.common.errors.ActionRefused import ActionRefused

from origin.actions.Actions import Actions


#
# Discard an item in your inventory. You can also drop or "discard all"
#
class Drop(Actions):

    @staticmethod
    @Actions.action("drop", "discard")
    def func(player, parsed, ctx):

        if not parsed.args:
            raise ParseError("What would you like to drop? You can also 'drop all' or 'drop everything'.")

        def drop(items, container):

            items = list(items)
            refused = []
            for item in items:
                try:
                    item.move(player.location, player, verb="drop")
                    if container is not player and container in player:
                        Drop.notify_item_removal(player, item, container)
                except ActionRefused as x:
                    refused.append((item, str(x)))

            for item, message in refused:
                items.remove(item)
                player.tell(message)

            if items:
                strItems = Lang.join(Lang.a(item.title) for item in items)
                player.tell("You discard <item>%s</item>." % strItems)
                player.tell_others("{Title} drops %s." % strItems)
            else:
                player.tell("Nothing was dropped.")

        arg = parsed.args[0]
        # drop all items?
        if arg == "all" or arg == "everything":
            drop(player.inventory, player)
        else:
            # drop a single item from inventory
            if parsed.obj_order:
                item = parsed.obj_order[0]
                if item in player:
                    drop([item], player)
                else:
                    raise ActionRefused("You can't seem to drop that!")
            # drop a container from inventory
            else:
                item, container = player.locate_item(arg, include_location=False)
                if item:
                    if container is not player:
                        Actions.print_object_location(player, item, container)
                    drop([item], container)
                else:
                    raise ActionRefused("You don't have <item>%s</item>." % Lang.a(arg))

    @classmethod
    def notify_item_removal(cls, player, item, container, print_parentheses=True):
        if print_parentheses:
            player.tell("(You take the %s from the %s)." % (item.name, container.name))
        else:
            player.tell("You take the %s from the %s." % (item.name, container.name))
        player.tell_others("{Title} takes the %s from the %s." % (item.name, container.name))