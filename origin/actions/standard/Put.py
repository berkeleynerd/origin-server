# coding=utf-8

from origin.parser import Lang

from origin.actions.Actions import Actions
from origin.common.errors.ParseError import ParseError
from origin.common.errors.ActionRefused import ActionRefused
from origin.objects.creatures.Creature import Creature


#
# Put an item or items into a container. If player isn't carrying the item they'll pick it up first.
#
class Put(Actions):

    @staticmethod
    @Actions.action("put", "place")
    def func(player, parsed, ctx):

        if len(parsed.args) < 2:
            raise ParseError("You need to tell me what to put and where you'd like to put it.")

        # If player specified all they want to put their entire inventory into the container
        if parsed.args[0] == "all":

            # Does the player have anything in their inventory
            if player.inventory_size == 0:
                raise ActionRefused("You don't seem to be carrying anything.")

            if len(parsed.args) != 2:
                raise ParseError("You need to tell me what to put and where you'd like to put it.")

            what = list(player.inventory)
            where = parsed.obj_order[-1]  # The last item represents the "where"

        elif parsed.unrecognized:
            raise ActionRefused("I don't see %s here." % Lang.join(parsed.unrecognized))

        else:
            what = parsed.obj_order[:-1]
            where = parsed.obj_order[-1]

        if isinstance(where, Creature):
            raise ActionRefused("You can't do that but you might be able to give it to them...")

        inventory_items = []
        refused = []

        word_before = parsed.obj_info[where].previous_word or "in"
        if word_before != "in" and word_before != "into":
            raise ActionRefused("You can only put an item 'in' or 'into' a container of some sort.")

        for item in what:
            if item is where:
                player.tell("You can't put something inside of itself.")
                continue

            try:
                # Are they using an item they are already carrying?
                if item in player:
                    item.move(where, player)
                    inventory_items.append(item)

                # If the item is in the room then we'll take it first and then put it into the container
                # TODO: We need to handle in a linguistic stylish way the situation where one part of this two-step operation fails
                elif item in player.location:
                    item.move(player, player)
                    item.move(where, player)
                    player.tell("You take %s and put it in the %s." % (item.title, where.name))
                    player.tell_others("{Title} takes %s and puts it in the %s." % (item.title, where.name))

            except ActionRefused as x:
                refused.append((item, str(x)))

        # The item refused to move at some point so inform the player
        for item, message in refused:
            player.tell(message)

        if inventory_items:
            items_msg = Lang.join(Lang.a(item.title) for item in inventory_items)
            player.tell_others("{Title} puts %s in the %s." % (items_msg, where.name))
            player.tell("You put <item>{items}</item> in the <item>{where}</item>.".format(items=items_msg, where=where.name))