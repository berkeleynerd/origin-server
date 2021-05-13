# coding=utf-8

from origin.actions.Actions import Actions
from origin.common.errors.ActionRefused import ActionRefused
from origin.objects.items.Item import Item


#
# Monitor messages within a 'location', to/from a creature, or 'off' to remove existing monitors.
#
class Monitor(Actions):

    @staticmethod
    @Actions.action("monitor")
    @Actions.sysop
    def func(player, parsed, ctx):

            if not parsed.args:
                raise ActionRefused("To monitor messages within a location use 'monitor location'. To monitor messages"
                                    "to and from a player use 'monitor [name]'. Use 'monitor off' to remove all existing"
                                    " monitors.")

            arg = parsed.args[0]
            if arg == "location":

                player.create_monitor(player.location)
                player.tell("Now monitoring location '<location>%s</location>'." % player.location.name)

            elif arg == "off":

                player.clear_monitors()
                player.tell("All monitors have been disabled.")

            elif parsed.obj_order:

                for creature in parsed.obj_order:

                    if creature is player:
                        raise ActionRefused("You can not monitor yourself.")

                    if isinstance(creature, Item):
                        raise ActionRefused("You can not monitor items.")

                    player.create_monitor(creature)
                    player.tell("Now monitoring player or creature <creature>%s</creature>." % creature.name)

            else:

                raise ActionRefused("Who would you like to monitor?")