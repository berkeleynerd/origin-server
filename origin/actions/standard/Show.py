# coding=utf-8

from origin.parser import Lang

from origin.actions.Actions import Actions
from origin.common.errors.ParseError import ParseError
from origin.common.errors.ActionRefused import ActionRefused


#
# Show an item in inventory to everyone in the same location or to another creature privately
#
class Show(Actions):

    @staticmethod
    @Actions.action("show", "reveal")
    def func(player, parsed, ctx):

        if len(parsed.obj_order) != 2:
            raise ParseError("What would you like to show and to whom?")

        shown = parsed.obj_order[0]
        if shown not in player:
            raise ActionRefused("You do not have <item>%s</item> to show." % Lang.a(shown.title))

        target = parsed.obj_order[1]
        player.tell("You reveal the <item>%s</item> to <creature>%s</creature>." % (shown.title, target.title))
        room_msg = "%s shows something to %s." % (Lang.capital(player.title), target.title)
        target_msg = "%s reveals the %s to you." % (Lang.capital(player.title), Lang.a(shown.title))
        player.location.tell(room_msg, exclude_creature=player, specific_target_msg=target_msg, specific_targets=[target])
