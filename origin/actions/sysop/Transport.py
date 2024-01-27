# coding=utf-8

import sys

from origin.actions.Actions import Actions
from origin.common.errors.ActionRefused import ActionRefused
from origin.objects.creatures.Creature import Creature
from origin.objects.locations.Location import Location


#
# Transports you to a location or another creature or transports a creature to you.
#
# ex: 'transport_self .region.room' transports you to the specified location or creature
# ex: 'transport [name]' transports you to the creature's location
# ex: 'transport start' transports you to the starting location for Sysops
#
class Transport(Actions):

    @staticmethod
    @Actions.action("transport", "transport_self")
    @Actions.sysop
    def func(player, parsed, ctx):

            if not parsed.args:
                raise ActionRefused("transport what to where?")

            args = parsed.args
            transport_self = parsed.verb == "transport_self"

            # Transport player to a specific location specified as a module path
            if args[0].startswith("."):

                path, objectname = args[0].rsplit(".", 1)

                if not objectname:
                    raise ActionRefused("Invalid module path.")

                # Let's find the specified module
                try:

                    module_name = "origin.adventure.regions"
                    if len(path) > 1:
                        module_name += path
                    __import__(module_name)
                    module = sys.modules[module_name]

                except (ImportError, ValueError):

                    raise ActionRefused("I can not find a module named " + path)

                target = getattr(module, objectname, None)
                if not target:
                    raise ActionRefused("I could not find the object %s in module %s" % (objectname, path))

                # Transport player to another creature's location
                if transport_self:

                    if isinstance(target, Creature):
                        target = target.location
                    if not isinstance(target, Location):
                        raise ActionRefused("I can not determine the location to transport you to.")
                    Transport.transport_to(player, target)

                else:

                    if isinstance(target, Location):
                        raise ActionRefused("I can't transport a room to your location but I can transport you to a location using 'transport_self [.region.room].")

                    Transport.transport_someone_to_player(target, player)

            else:

                # Is the specified target the Sysop start location?
                if args[0] == "start":
                    Transport.transport_to(player, ctx.config.sysop_start)

                # If not, the player must want to teleport to another creature's location
                else:

                    target = ctx.engine.search_player(args[0])

                    if not target:
                        raise ActionRefused("%s doesn't appear to be online." % args[0])

                    if transport_self:
                        Transport.transport_to(player, target.location)
                    else:
                        Transport.transport_someone_to_player(target, player)


    #
    # Handles the scenario of transporting the player making the request somehwere else
    #
    @staticmethod
    def transport_to(player, location):

        player.transported_from = player.location  # supports the 'return' action
        player.move(location, silent=False)
        player.look()


    #
    # Handles the scenario of transporting another creature to the player's current location
    #
    @staticmethod
    def transport_someone_to_player(who, player):

        who.transported_from = who.location  # supports the 'return' action
        who.move(player.location, silent=False)