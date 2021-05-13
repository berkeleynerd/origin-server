# coding=utf-8

from origin.common.errors.ParseError import ParseError
from origin.common.errors.ActionRefused import ActionRefused

from origin.actions.Actions import Actions
from origin.parser import Lang
from origin.objects.creatures.Creature import Creature


#
# Give an item or all items in inventory to another creature.
#
class Give(Actions):

    @staticmethod
    @Actions.action("give")
    def func(player, parsed, ctx):

            if len(parsed.args) < 2:
                raise ParseError("You must specify what to give and whom to give it to.")

            if parsed.unrecognized or player.inventory_size == 0:
                raise ParseError("You don't have %s to give." % Lang.join(parsed.unrecognized))

            # Does the player want to give everything they have?
            if "all" in parsed.args:

                if len(parsed.args) != 2:
                    raise ParseError("You must specify who you want to give the items to.")

                what = player.inventory

                if parsed.args[0] == "all":
                    Give.give_all(player, what, parsed.args[1])
                    return
                else:
                    Give.give_all(player, what, parsed.args[0])
                    return

            # Player wants to give just a single item
            if len([who for who in parsed.obj_order if isinstance(who, Creature)]) > 1:
                # if there's more than one creature, it's not clear who to give stuff to
                raise ActionRefused("It's not clear who you want to give things to.")

            # if the first parsed word is a creature assume the syntax "give creature [the] thing(s)"
            if isinstance(parsed.obj_order[0], Creature):
                what = parsed.obj_order[1:]
                Give.give_all(player, what, None, target=parsed.obj_order[0])
                return

            # if the last parsed word is a creature assume the syntax "give thing(s) [to] creature"
            elif isinstance(parsed.obj_order[-1], Creature):
                what = parsed.obj_order[:-1]
                Give.give_all(player, what, None, target=parsed.obj_order[-1])
                return

            else:
                raise ActionRefused("It's not clear to who you want to give the item.")


    @staticmethod
    def give_all(player, items, target_name, target=None):

        if not target:
            target = player.location.search_creature(target_name)
        if not target:
            raise ActionRefused("%s isn't here with you." % target_name)
        if target is player:
            raise ActionRefused("Giving something to yourself doesn't make much sense.")

        # Actually try to give the items...
        items = list(items)
        refused = []
        for item in items:
            try:
                item.move(target, player)
            except ActionRefused as x:
                refused.append((item, str(x)))

        # Let the player know why giving a particular item failed
        for item, message in refused:
            player.tell(message)
            items.remove(item)

        if items:
            items_str = Lang.join(Lang.a(item.title) for item in items)
            player_str = Lang.capital(player.title)
            room_msg = "<player>%s</player> gives <item>%s</item> to <creature>%s</creature>." % (player_str, items_str, target.title)
            target_msg = "<player>%s</player> gives you <item>%s</item>." % (player_str, items_str)
            player.location.tell(room_msg, exclude_creature=player, specific_targets=[target], specific_target_msg=target_msg)
            player.tell("You give <creature>%s</creature> <item>%s</item>." % (target.title, items_str))

        else:
            player.tell("You weren't able to give <creature>%s</creature> anything." % target.title)