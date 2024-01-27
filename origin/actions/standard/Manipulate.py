# coding=utf-8

from origin.common.errors.RetryVerb import RetryVerb
from origin.common.errors.ParseError import ParseError
from origin.common.errors.ActionRefused import ActionRefused

from origin.actions.Actions import Actions
from origin.parser import Lang


#
# Manipulate an item.
#
class Manipulate(Actions):

    @staticmethod
    @Actions.action("move", "shove", "swivel", "shift", "manipulate", "manip", "press", "poke", "push", "prod")
    def func(player, parsed, ctx):

        # Poor man's autocomplete :)
        if parsed.verb == "manip":
            parsed.verb = "manipulate"

        if len(parsed.obj_order) == 1:
            what = parsed.obj_order[0]
            try:
                what.manipulate(parsed.verb, player)
                return
            except ActionRefused:
                raise

        raise ParseError("What would you like to %s?" % Lang.capital(parsed.verb))