# coding=utf-8

from origin.actions.Actions import Actions
from origin.actions.standard.Activate import Activate
from origin.actions.standard.Deactivate import Deactivate

from origin.actions.standard.Manipulate import Manipulate
from origin.common.errors.ParseError import ParseError


#
# Turn or rotate an item. Variation on Activate and Deactivate.
#
class Turn(Actions):

    @staticmethod
    @Actions.action("turn", "rotate")
    def func(player, parsed, ctx):

        if len(parsed.obj_order) == 1:

            who = parsed.obj_order[0]
            if parsed.obj_info[who].previous_word == "on" or parsed.unparsed.endswith(" on"):
                Activate.func(player, parsed, ctx)
                return
            elif parsed.obj_info[who].previous_word == "off" or parsed.unparsed.endswith(" off"):
                Deactivate.func(player, parsed, ctx)
                return

        elif len(parsed.obj_order) == 0:
            arg = parsed.unparsed.partition(" ")[0]
            if arg in ("on", "off"):
                raise ParseError("What are you trying to switch %s?" % arg)

        # Rather than switch something on or off they could be using the word turn in a more general sense as to
        # manipulate something in a particular way...
        Manipulate.func(player, parsed, ctx)