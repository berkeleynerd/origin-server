# coding=utf-8

from origin.parser import Lang

from origin import context
from origin.common.errors.LocationIntegrityError import LocationIntegrityError
from origin.engine.pubsub.Topic import Topic
from origin.objects.ObjectBase import ObjectBase
from origin.objects.creatures.Creature import Creature
from origin.objects.items.Item import Item

#
# Represents a location within the game. It contains Creature and Item objects and connects to other
# locations via Exit objects. You can check to see if a location contains an object using, for example,
# 'if player in location:'
#
class Location(ObjectBase):

    _void = None

    def __init__(self, name, description=None, region="convent", varname=None):

        super(Location, self).__init__(name, description=description)

        # Preserve original case as the base object converts names to lowercase for consistency
        self.name = name

        # Creatures in the location stored as a set
        self.creatures = set()

        # Items in the room stored as a set
        self.items = set()

        # Exits bound to the location stored as a dictionary
        # An exit_direction represents an Exit object including location target and description
        self.exits = {}

        if varname is None:
            self.varname = name.lower()
        else:
            self.varname = varname

        self.region = region


    def __contains__(self, obj):
        return obj in self.creatures or obj in self.items


    def __getstate__(self):
        state = dict(self.__dict__)
        return state


    def __setstate__(self, state):
        self.__dict__ = state


    @staticmethod
    def void():

        if Location._void is None:
            Location._void = Location("Void", "Nothingness.")

        return Location._void


    #
    # Initialize items and creatures found in this location
    #
    def init_inventory(self, objects):

        if len(self.items) > 0 or len(self.creatures) > 0:
            raise LocationIntegrityError("Location already contains items or creatures. ", None, None, self)

        for obj in objects:
            self.insert(obj, self)


    #
    # Clear / release all resources associated with this location
    #
    def destroy(self, ctx):

        super(Location, self).destroy(ctx)

        for creature in self.creatures:
            if creature.location is self:
                creature.location = Location._void

        self.creatures.clear()
        self.items.clear()
        self.exits.clear()


    #
    # Bind exits to this location.
    #
    def add_exits(self, exits):

        # Since an exit may have aliases we need to bind them as well.
        for exit in exits:
            exit.bind(self)


    #
    # Provides a monitor for this location.
    #
    def get_monitor(self):
        return Topic.static_topic(("monitor-location", self.name))


    #
    # Broadcasts a message to all creatures in the room except those indicated by exclude_creature.
    # This should only be used for messaging. Generally, use process_action and notify_action instead.
    # Objects monitoring activity in a room are also notified.
    #
    def tell(self, room_msg, exclude_creature=None, specific_targets=None, specific_target_msg=""):

        specific_targets = specific_targets or set()
        assert isinstance(specific_targets, (frozenset, set, list, tuple))

        # Make sure anything listed to exclude is a Creature
        if exclude_creature:
            assert isinstance(exclude_creature, Creature)

        for creature in self.creatures:

            # Skip broadcasting to anyone specifically excluded
            if creature == exclude_creature:
                continue

            # Send specific objects get specific messages we'll handle that condition as well
            if creature in specific_targets:
                creature.tell(specific_target_msg)
            else:
                creature.tell(room_msg)

        # Send the room message to any objects monitoring room activity
        if room_msg:
            monitor = self.get_monitor()
            monitor.send((self.name, room_msg))


    #
    # Broadcasts a message to locations connected to this location via bound Exit objects.
    # If an Exit includes a cardinal direction binding (north, south, east, west, up, down)
    # the direction from which the sound originates will also be indicated. Use this for loud
    # noises. For example usage see the 'Yell' action.
    #
    def tell_adjacent_locations(self, message):

        if self.exits:

            told_locations = set()

            for exit in self.exits.values():

                # Since more than one Exit can lead to the same destination location
                # avoid sending the message more than onece...
                if exit.target in told_locations:
                    continue

                # If an Exit leads immediately back to this location don't display the message again.
                if exit.target is not self:

                    # Send the message and add it to the list of locations that have received it
                    exit.target.tell(message)
                    told_locations.add(exit.target)

                    # If applicable (e.g., Exit includes a cardinal direction), indicate the direction
                    # from which the sound originates.
                    for direction, return_exit in exit.target.exits.items():

                        if return_exit.target is self:

                            if direction in {"north", "east", "south", "west", "northeast", "northwest", "southeast",
                                             "southwest", "left", "right", "front", "back"}:
                                direction = "the " + direction
                            elif direction in {"up", "above", "upstairs"}:
                                direction = "above"
                            elif direction in {"down", "below", "downstairs"}:
                                direction = "below"
                            else:
                                continue  # no direction description possible for this exit

                            exit.target.tell("The sound seems to be coming from %s." % direction)

                            break

                    # Otherwise just let the player know the sound is coming from some distance away and encourage them
                    # to explore.
                    else:
                        exit.target.tell("The sound is emmanating from some distance away but you can't determine from"
                                         " which diretion.")


    #
    # Returns an iterable set of all adjacent locations excluding those without a way back.
    #
    def nearby(self, no_traps=True):

        if no_traps:
            return (e.target for e in self.exits.values() if e.target.exits)

        return (e.target for e in self.exits.values())


    #
    # Provides a description of a location including any creatures, items, and exits it contains.
    # You can exclude a particular creature, such as the player themselves, using the exclude_creature parameter
    #
    def look(self, exclude_creature=None, short=False):

        paragraphs = ["<location>[" + self.name + "]</location>"]

        # Construct the short version of a location description.
        if short:

            if self.exits and context.config.show_exits_in_look:
                paragraphs.append("<exit>Exits</exit>: " + ", ".join(sorted(set(self.exits.keys()))))

            if self.items:
                item_names = sorted(item.name for item in self.items)
                paragraphs.append("<item>You see</item>: " + Lang.join(item_names))

            if self.creatures:
                creature_names = sorted(creature.name for creature in self.creatures if creature != exclude_creature)
                if creature_names:
                    paragraphs.append("<creature>Present</creature>: " + Lang.join(creature_names))

            return paragraphs

        #
        # Construct the long version of a location description.
        #

        if self.description:
            paragraphs.append(self.description)

        if self.exits and context.config.show_exits_in_look:

            # Keep track of exits we've already described
            exits_seen = set()
            exit_paragraph = []

            for exit_name in sorted(self.exits):

                exit = self.exits[exit_name]

                if exit not in exits_seen:
                    exits_seen.add(exit)
                    exit_paragraph.append(exit.short_description)

            paragraphs.append(" ".join(exit_paragraph))

        items_and_creatures = []

        # We'll preferentially use item short descriptions if provided and resort to the item's title if necessary
        items_with_short_descr = [item for item in self.items if item.short_description]
        items_without_short_descr = [item for item in self.items if not item.short_description]
        uniq_descriptions = set()

        # If there's a short description for an item use it preferentially
        if items_with_short_descr:
            for item in items_with_short_descr:
                uniq_descriptions.add(item.short_description)

        # Add unique item description to our running list of things to describe
        items_and_creatures.extend(uniq_descriptions)

        # If there's no short description for an item we'll just use the item's title
        if items_without_short_descr:
            titles = sorted([Lang.a(item.title) for item in items_without_short_descr])
            items_and_creatures.append("You see " + Lang.join(titles) + ".")

        # We'll preferentially use creature short descriptions if provided and resort to the title if necessary
        creatures_with_short_descr = [creature for creature in self.creatures
                                      if creature != exclude_creature and creature.short_description]
        creatures_without_short_descr = [creature for creature in self.creatures
                                         if creature != exclude_creature and not creature.short_description]

        # If there's a short descriptions for a creature use it preferentially
        if creatures_without_short_descr:
            titles = sorted(creature.title for creature in creatures_without_short_descr)
            if titles:
                titles_str = Lang.join(titles)
                if len(titles) > 1:
                    titles_str += " are here."
                else:
                    titles_str += " is here."
                items_and_creatures.append(Lang.capital(titles_str))
        uniq_descriptions = set()

        # If there's no short description for a creature we'll just use the item's title
        if creatures_with_short_descr:
            for creature in creatures_with_short_descr:
                uniq_descriptions.add(creature.short_description)

        # Add unique creature descriptions to our running list of things to describe
        items_and_creatures.extend(uniq_descriptions)
        if items_and_creatures:
            paragraphs.append(" ".join(items_and_creatures))

        return paragraphs


    #
    # Search for a particular creature by its name or, if there's no match, it's title
    # Since a creature can have aliases we just return the first match
    #
    def search_creature(self, name):

        name = name.lower()
        result = [creature for creature in self.creatures if creature.name == name]

        # If no direct match we'll try any aliases and, finally, the title
        if not result:
            result = [creature for creature in self.creatures if name in creature.aliases or creature.title.lower() == name]

        return result[0] if result else None


    #
    # Place a creature or item into the location
    #
    def insert(self, obj, actor):

        if isinstance(obj, Creature):
            self.creatures.add(obj)
        elif isinstance(obj, Item):
            self.items.add(obj)
        else:
            raise TypeError("Only creatures or items can be added to a location.")

        obj.location = self


    #
    # Remove a creature or item from the location
    #
    def remove(self, obj, actor):

        if obj in self.creatures:
            self.creatures.remove(obj)
        elif obj in self.items:
            self.items.remove(obj)
        else:
            return

        obj.location = None


    #
    # Process a custom action.
    #
    def process_action(self, parsed, actor):

        # Raise an AsyncDialog exception to indicate to the engine that it should kickstart the
        # specified async dialog as a workaround to handling yields directly.
        handled = any(creature._process_action_base(parsed, actor) for creature in self.creatures)

        if not handled:
            handled = any(item.process_action(parsed, actor) for item in self.items)
            if not handled:
                handled = any(exit.process_action(parsed, actor) for exit in set(self.exits.values()))

        return handled


    #
    # Notify the location and its contents of an action performed by an actor
    #
    def notify_action(self, parsed, actor):

        # Notification actions are invoked after all player input has been processed to avoid
        # queing delegated calls.

        for creature in self.creatures:
            creature._notify_action_base(parsed, actor)

        for item in self.items:
            item.notify_action(parsed, actor)

        for exit in set(self.exits.values()):
            exit.notify_action(parsed, actor)


    def notify_npc_arrived(self, npc, previous_location):
        pass


    def notify_npc_left(self, npc, target_location):
        pass


    def notify_player_arrived(self, player, previous_location):
        pass

    def notify_player_left(self, player, target_location):
        pass
