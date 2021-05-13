# coding=utf-8

from origin.parser import Lang

from origin.actions.Actions import Actions
from origin.common.errors.ParseError import ParseError
from origin.common.errors.ActionRefused import ActionRefused
from origin.objects.creatures.Creature import Creature
from origin.objects.exits.Exit import Exit


#
#  Take one or more items from a container or another player or NPC.
#
class Get(Actions):

    @staticmethod
    @Actions.action("take", "get")
    def func(player, parsed, ctx):

        # Did the player specify something to be taken?
        if len(parsed.args) == 0:
            raise ParseError("What would you like to take?")

        # Player is taking a single item
        if len(parsed.args) == 1:
            obj_names = parsed.args
            where = None

        # Player wants to try something more complicated...
        else:

            if parsed.obj_order:

                last_obj = parsed.obj_order[-1]

                # Player is trying to take one or more (comma separated) items from something or someone
                if parsed.obj_info[last_obj].previous_word == "from":
                    obj_names = parsed.args[:-1]
                    where = last_obj

                # Player is trying to take one or more (comma separated) items
                else:
                    # take x[,y and z]
                    obj_names = parsed.args
                    where = None

            else:
                # take x[,y and z] - unrecognised names
                obj_names = parsed.args
                where = None

        # Basic sanity check
        if where is player:
            raise ActionRefused("You can't take items from yourself.")

        # Notify others in the room that something is creature taken
        if isinstance(where, Creature):
            player.tell_others("{Title} takes something from %s." % where.title)

        # Player wants to take all teh things
        if obj_names == ["all"]:

            # Are we taking items from a container?
            if where:

                # Is the container on the player's person or in the room with the player?
                if where in player or where in player.location:

                    # Is there anything in it?
                    if where.inventory_size > 0:
                        Get.take_all(player, where.inventory, where, where.title)
                        return
                    else:
                        raise ActionRefused("It appears to be empty.")

                raise ActionRefused("What are you trying to take?")

            # We're taking items from the room the player is in
            else:

                # Anything here to take?
                if not player.location.items:
                    raise ActionRefused("There appears to be nothing here you can carry.")
                # Yes, so dump everything into the player's inventory.
                else:
                    Get.take_all(player, player.location.items, player.location)
                    return

        # Player is trying to take one or more specific items
        else:

            # Are we taking items from a container?
            if where:

                # Yes, is the container on the player's person or in the room?
                if where in player or where in player.location:

                    # Take each item from the specified container
                    items_by_name = {item.name: item for item in where.inventory}
                    items_to_take = []

                    for name in obj_names:

                        # If it's there let's take it...
                        if name in items_by_name:
                            items_to_take.append(items_by_name[name])
                        # ...otherwise tell the player their action is misguided.
                        else:
                            player.tell("There's no %s in there." % name)

                    Get.take_all(player, items_to_take, where, where.title)
                    return
            else:

                # Looks like the player is trying to take items from the room itself
                if parsed.unrecognized:
                    player.tell("You don't see %s here." % Lang.join(parsed.unrecognized))

                creatures = [item for item in parsed.obj_order if item in player.location.creatures]
                for creature in creatures:
                    player.tell("You can not pick up other living creatures.")

                if not player.location.items:
                    raise ActionRefused("There appears to be nothing here you can carry.")

                else:

                    items_to_take = []
                    for item in parsed.obj_order:

                        # If item is here let the player take it!
                        if item in player.location.items:
                            items_to_take.append(item)

                        # If the item is an exit let's remind the user it can't be taken
                        elif isinstance(item, Exit):
                            raise ActionRefused("That is not something you can carry.")

                        elif item not in player.location.creatures:
                            if item in player:
                                player.tell("You already have that item.")
                            else:
                                player.tell("There's no <item>%s</item> here." % item.name)

                    Get.take_all(player, items_to_take, player.location)
                    return

    # Actually takes items and returned the number of items taken
    @staticmethod
    def take_all(player, items, container, where_str=None):

        # No items were specified
        if not items:
            return 0

        # Is player taking something from a container?
        if where_str:
            player_msg = "You take <item>{items}</item> from the <item>%s</item>" % where_str
            room_msg = "<player>{{Title}}</player> takes <item>{items}</item> from the <item>%s</item>" % where_str

        # If not, they must be taking it from the room
        else:
            player_msg = "You take <item>{items}</item>"
            room_msg = "<player>{{Title}}</player> takes <item>{items}</item>"

        items = list(items)
        refused = []
        # Try to move items one by one. If there are special rules against taking them the item should
        # raise an ActionRefused exception.
        for item in items:
            try:
                item.move(player, player, verb="take")
            except ActionRefused as x:
                refused.append((item, str(x)))

        # Tell player if any items refused to budge
        for item, message in refused:
            player.tell(message)
            items.remove(item)

        # Tell player about any items that were moved into their inventory
        # and tell nearby players and NPCs abou it too!
        if items:
            items_str = Lang.join(Lang.a(item.title) for item in items)
            player.tell(player_msg.format(items=items_str))
            player.tell_others(room_msg.format(items=items_str))
            return len(items)
        else:
            return 0