# coding=utf-8

from origin.actions.Actions import Actions


#
# Displays a list of all the items the player is carrying
#
class Inventory(Actions):

    @staticmethod
    @Actions.disable_notify
    @Actions.action("inventory", "inv", "i")
    def func(player, parsed, ctx):

        if parsed.obj_order and player.isSysOp:

            # A Sysop can examine anything's inventory
            other = parsed.obj_order[0]
            other.show_inventory(player, ctx)

        else:

            inventory = player.inventory
            if inventory:
                msg = "You are carrying "
                for item in inventory:
                    msg += "<item>%s</item>, " % item.title
                msg = msg[:-2]
                player.tell(msg)
            else:
                player.tell("You don't seem to be carrying anything.")
