# coding=utf-8

from origin.parser import Lang

from origin.actions.Actions import Actions
from origin.common.errors.ParseError import ParseError
from origin.common.errors.ActionRefused import ActionRefused
from origin.objects.creatures.Creature import Creature


#
# Manipulate an exit or item possibly using san item like a key
#
class Open(Actions):

    @staticmethod
    @Actions.action("open", "close", "lock", "unlock")
    def func(player, parsed, ctx):

        if len(parsed.args) not in (1, 2) or parsed.unrecognized:
            raise ParseError("What are you trying to %s?" % Lang.capital(parsed.verb))

        if parsed.obj_order:
            if isinstance(parsed.obj_order[0], Creature):
                raise ActionRefused("You can't do that to other living creatures.")

        obj_name = parsed.args[0]

        # Is the player using something to try to manipulate the object?
        with_item_name = None
        with_item = None
        if len(parsed.args) == 2:
            with_item_name = parsed.args[1]

        what = player.search_item(obj_name, include_inventory=True, include_location=True, include_containers=False)
        # Are we dealing with an exit?
        if not what:
            if obj_name in player.location.exits:
                what = player.location.exits[obj_name]

        # Are we dealing with an item?
        if what:
            # If so, are they using an item to accomplish the manipulation?
            if with_item_name:
                with_item = player.search_item(with_item_name, include_inventory=True, include_location=False, include_containers=False)
                if not with_item:
                    raise ActionRefused("You don't seem to have <item>%s</item>." % Lang.a(with_item_name))

            getattr(what, parsed.verb)(player, with_item)

        else:
            raise ActionRefused("You don't see that here.")