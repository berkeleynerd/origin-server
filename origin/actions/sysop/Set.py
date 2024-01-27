# coding=utf-8

from origin.actions.Actions import Actions
from origin.common.errors.ActionRefused import ActionRefused
from origin.common.errors.ParseError import ParseError


#
# Create a new attribute and assign it a value or change the value of an existing attribute.
# Usage : set object.attribute=value
# Values are limited to Python literals. Applies to any object derived from ObjectBase. Limited to player's location.
#
class Set(Actions):

    @staticmethod
    @Actions.action("set")
    @Actions.sysop
    def func(player, parsed, ctx):

        if not parsed.args:
            raise ParseError("usage: set object.attribute=value")

        args = parsed.args[0].split("=")
        if len(args) != 2:
            raise ParseError("usage: set object.attribute=value")

        name, field = args[0].split(".")

        # Player location?
        if name == "":
            obj = player.location
        # An item in the player's inventory or current location?
        else:
            obj = player.search_item(name, include_inventory=True, include_location=True)

        # A creature in the player's location?
        if not obj:
            obj = player.location.search_creature(name)

        if not obj:
            raise ActionRefused("I can not find the object you specified.")

        player.tell(repr(obj))

        import ast

        value = ast.literal_eval(args[1])
        expected_type = type(getattr(obj, field))

        if expected_type is type(value):
            setattr(obj, field, value)
            player.tell("Object %s attribute %s set to %r" % (name, field, value))
        else:
            raise ActionRefused("I expected a %s value type." % expected_type)