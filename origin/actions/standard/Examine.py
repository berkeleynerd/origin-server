# coding=utf-8

from origin.parser import Lang
from origin.common.errors.ParseError import ParseError
from origin.common.errors.ActionRefused import ActionRefused

from origin.actions.Actions import Actions
from origin.objects.creatures.Creature import Creature


#
# Examine something or someone thoroughly.
#
class Examine(Actions):

    @staticmethod
    @Actions.action("examine", "inspect")
    @Actions.disable_notify
    def func(player, parsed, ctx):

        # If we're examining a creature let's get some info for it
        creature = None
        if parsed.obj_info and isinstance(parsed.obj_order[0], Creature):
            creature = parsed.obj_order[0]
            name = creature.name

        # If we're not examining a creature we'll get item info
        if not creature:

            # Handle the case where nothing to examine was specified
            if not parsed.args:
                raise ParseError("Who or what would you like to examine?")

            Actions.parse_is_are(parsed.args)
            name = parsed.args[0]
            creature = player.location.search_creature(name)

        # If we're trying to examine a creature we'll figure out
        # which creature we're dealing with
        if creature:

            # Player is trying to examine themselves. Sheesh.
            if creature is player:
                player.tell("You are <creature>%s</creature>." % Lang.capital(creature.title))
                return

            if creature.name.lower() != name.lower() and name.lower() in creature.aliases:
                player.tell("(By %s you probably meant %s.)" % (name, creature.name))

            # If the creature has a description show the player otherwise we'll just share their title
            if creature.description:
                player.tell(creature.description)
            else:
                player.tell("This is <creature>%s</creature>." % creature.title)

            # If there is extended info about the creature we'll provide that as well
            if name in creature.extra_desc:
                player.tell(creature.extra_desc[name])

            if name in player.location.extra_desc:
                player.tell(player.location.extra_desc[name])

            return

        # Is the player trying to examine an item?
        item, container = player.locate_item(name)
        if item:

            if item.name.lower() != name.lower() and name.lower() in item.aliases:
                player.tell("Maybe you meant %s?" % item.name)

            # If there is an extended description we'll share that.
            if name in item.extra_desc:
                player.tell(item.extra_desc[name])
            # Otherwise we'll just share what basic info we have
            else:
                if item in player:
                    player.tell("You're carrying <item>%s</item>." % Lang.a(item.title))
                elif container and container in player:
                    Actions.print_object_location(player, item, container)
                else:
                    player.tell("You see <item>%s</item>." % Lang.a(item.title))
                if item.description:
                    player.tell(item.description)

            try:
                inventory = item.inventory
            except ActionRefused:
                pass
            else:
                if inventory:
                    msg = "It contains "
                    for item in inventory:
                        msg += "<item>%s</item>, " % item.title
                    msg = msg[:-2]
                    player.tell(msg)
                else:
                    player.tell("It's empty.")

        # Player is examining an exit?
        elif name in player.location.exits:
            player.tell("<exit>" + player.location.exits[name].description + "</exit> represents a way you can travel to a different place.")

        # If nothing else we'll do a search for any extended descriptive info associated with
        # locations and items
        else:
            text = player.search_extradesc(name)
            if text:
                player.tell(text)
            else:
                raise ActionRefused("%s doesn't appear to be here." % name)