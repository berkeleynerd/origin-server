# coding=utf-8

from origin.common.errors.ActionRefused import ActionRefused
from origin.common.errors.LocationIntegrityError import LocationIntegrityError

from origin import context
from origin.objects.ObjectBase import ObjectBase
from origin.objects.locations.Location import Location


#
# EXIT
#     Represents a one-way connection between two locations.
#
# DIRECTION
#     Either a single string or a sequence of DIRECTIONS all referring to the same EXIT.
#
# TARGET
#     Either a Location object or a string referring to a location.
#     E.g., the string 'convent.garden' refers to the 'garden' Location object in 'adventure.regions.convent'.
#     When using a string the object is instanced and bound to a region at runtime.
#
# Short_description
#     Displayed when the player looks within a location.
#
# Long_description
#     An optional longer description displayed when a player examines an exit.
#
# Name
#     An exit's direction is represented by its name attribute with aliases representing parsable alternative.
#
# An exit's origin is not stored within an exit object.
#
class Exit(ObjectBase):


    def __init__(self, directions, target_location, short_description, long_description=None):

        assert isinstance(target_location, (Location, str)), \
            "A target must be either a Location object or a string referring to a location."

        # Are we dealing with a single string?
        if isinstance(directions, str):
            direction = directions
            aliases = frozenset()
        # If not, we're dealing with a list of strings including potential aliases.
        else:
            direction = directions[0]
            aliases = frozenset(directions[1:])

        self.target = target_location
        self.bound = isinstance(target_location, Location)
        if self.bound:
            title = "Exit to " + self.target.title
        else:
            title = "Exit to <unbound:%s>" % self.target

        # Long description will default to short description if not long_description is provided
        long_description = long_description or short_description

        # Initialize our superclass, ObjectBase
        super(Exit, self).__init__(direction, title=title, description=long_description, short_description=short_description)

        # Aliases are alternative ways for the player to refer to this exit. E.g., "gate", "portcullis", etc...
        self.aliases = aliases

        # Register the exit with the game engine.
        context.engine.register_exit(self)


    def __repr__(self):
        targetname = self.target.name if self.bound else self.target
        return "<base.Exit to '%s' @ 0x%x>" % (targetname, id(self))


    #
    # Bind the exit to a location
    #
    def bind(self, location):

        assert isinstance(location, Location)

        # Create a set including the exit's name and any aliases.
        directions = self.aliases | {self.name}

        # Create a binding for each direction specified
        for direction in directions:

            if direction in location.exits:
                raise LocationIntegrityError("The exit '%s' is already bound to %s" % (direction, location), direction, self, location)

            location.exits[direction] = self


    #
    # Allows the engine to bind an exit to a location object dynamically before the first player enters the world.
    # We need access to the root module of the game's regions to avoid circular import references.
    # TODO: Let's try to do this un-dynamically for the sake of simplicity. The code is too meta / complex for our use.
    #
    def _bind_target(self, regions_module):

        if not self.bound:

            target_module, target_object = self.target.rsplit(".", 1)
            module = regions_module

            try:
                for name in target_module.split("."):
                    module = getattr(module, name)
                target = getattr(module, target_object)
            except AttributeError:
                raise AttributeError("I can't find location '%s.%s' in exit '%s'"
                                     % (target_module, target_object, self.short_description))

            assert isinstance(target, Location)

            self.target = target
            self.title = "Exit to " + target.title
            self.name = self.title.lower()
            self.bound = True


    #
    # Determine if a creature is allowed to pass through the exit.
    # Override to provide behavior specific to a particular exit.
    #
    def allow_passage(self, actor):
        if not self.bound:
            raise LocationIntegrityError("This exit appears to be closed for repairs.", None, self, None)


    #
    # Generic base class implementation for open action.
    #
    def open(self, actor, item=None):
        raise ActionRefused("It doesn't seem to open.")


    #
    # Generic base class implementation for close action.
    #
    def close(self, actor, item=None):
        raise ActionRefused("It's not something you can close.")


    #
    # Generic base class implementation for lock action.
    #
    def lock(self, actor, item=None):
        raise ActionRefused("It can't be locked.")


    #
    # Generic base class implementation for unlock action.
    #
    def unlock(self, actor, item=None):
        raise ActionRefused("It can't be unlocked.")


    #
    # Generic base class implementation for manipulate action.
    #
    def manipulate(self, verb, actor):
        raise ActionRefused("I don't understand what %s means in this context." % verb)