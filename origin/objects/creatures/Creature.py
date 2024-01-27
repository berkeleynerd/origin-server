# coding=utf-8

from origin.parser import Lang
from origin.common.errors.ActionRefused import ActionRefused
from origin.common.errors.ParseError import ParseError

from origin.actions.Actions import Actions
from origin.engine.pubsub.Topic import Topic
from origin.objects.ObjectBase import ObjectBase
from origin.objects.items.Item import Item
from origin.common.errors.NotDefaultVerb import NotDefaultVerb
from origin.parser.Parser import Parser


#
# Base class for all creatures. Creatures can have a heartbeat which allows them to
# act within the game context and an inventory that can hold Item object instances.
#
class Creature(ObjectBase):


    def __init__(self, name, gender, title=None, description=None, short_description=None):

        # TODO: Uncertain why this import must happen within __init__
        from origin.objects.locations.Location import Location

        self.init_gender(gender)
        self.parser = Parser()
        self.location = Location.void()
        self.isSysOp = False
        self.default_verb = "examine"
        self.__inventory = set()
        self.previous_actionline = None
        self._previous_parsed = None

        super(Creature, self).__init__(name, title, description, short_description)


    def init_gender(self, gender):

        self.gender = gender
        self.subjective = Lang.SUBJECTIVE[self.gender]
        self.possessive = Lang.POSSESSIVE[self.gender]
        self.objective = Lang.OBJECTIVE[self.gender]


    def init_inventory(self, items):
        for item in items:
            self.insert(item, self)


    def __getstate__(self):
        state = dict(self.__dict__)
        return state


    def __setstate__(self, state):
        self.__dict__ = state


    def __contains__(self, item):
        return item in self.__inventory


    @property
    def inventory_size(self):
        return len(self.__inventory)


    @property
    def inventory(self):
        return frozenset(self.__inventory)


    #
    # Give an item to the creature
    #
    def insert(self, item, actor):

        if isinstance(item, Item) and (actor is self or actor is not None and actor.isSysOp):
            self.__inventory.add(item)
            item.contained_in = self
        else:
            raise ActionRefused("That item can not be given to this creature.")


    #
    # Take an item from the creature
    #
    def remove(self, item, actor):

        if actor is self or actor is not None and actor.isSysOp:
            self.__inventory.remove(item)
            item.contained_in = None
        else:
            raise ActionRefused("You can not take %s from %s." % (item.title, self.title))


    #
    # Releaes all resources associated with an instance of the Creature class
    #
    def destroy(self, ctx):

        super(Creature, self).destroy(ctx)

        if self.location and self in self.location.creatures:
            self.location.creatures.remove(self)

        self.location = None

        for item in self.__inventory:
            item.destroy(ctx)

        self.__inventory.clear()

        self.parser = None


    @ObjectBase.authorized()
    def sys_clone(self, actor):

        duplicate = ObjectBase.clone(self)
        actor.tell("Creature cloned to " + repr(duplicate))
        actor.location.insert(duplicate, actor)
        actor.location.tell("%s appears." % Lang.capital(duplicate.title))
        return duplicate


    @ObjectBase.authorized()
    def sys_destroy(self, actor, ctx):

        if self is actor:
            raise ActionRefused("You can not destroy your self.")

        self.destroy(ctx)


    #
    # show the creature's inventory to the actor
    #
    def show_inventory(self, actor, ctx):

        name = Lang.capital(self.title)

        if self.inventory:
            actor.tell(name, "is carrying the following items:")
            for item in self.inventory:
                actor.tell("  " + item.title)
        else:
            actor.tell(name, "does not appear to have anything on them.")


    #
    # Monitor the creature's behavior
    #
    def get_monitor(self):

        return Topic.static_topic(("monitor-creature", self.name))


    #
    # Every creature can receive messages. In the case of players messages are transmitted to their client.
    # The default for NPC creatures is to ignore any messages they receive.
    #
    def tell(self, *messages):

        msg = " ".join(str(msg) for msg in messages)
        tap = self.get_monitor()
        tap.send((self.name, msg))


    #
    # Send a message to the creature but only after all other messages have been sent.
    #
    def tell_later(self, *messages):
        ObjectBase.pending_tells.send(lambda: self.tell(*messages))


    #
    # Send one or more messages to other creatures in this creature's location
    # {title}/{Title} can be used to conveniently insert an object's title
    #
    def tell_others(self, *messages):

        formats = {"title": self.title, "Title": Lang.capital(self.title)}
        for msg in messages:
            msg = msg.format(**formats)
            self.location.tell(msg, exclude_creature=self)


    def parse(self, actionline, external_verbs=frozenset()):

        parsed = self.parser.parse(self, actionline, external_verbs)
        self._previous_parsed = parsed

        if external_verbs and parsed.verb in external_verbs:
            raise NotDefaultVerb(parsed)

        return parsed


    #
    # Remember the previously parsed data. We can use this to reference back to previous objects
    #
    def remember_parsed(self):

        self.parser.previously_parsed = self._previous_parsed


    #
    # Perform an action at the behest of another actor, likely a Sysop.
    #
    # This code is similar to __process_player_action from the engine proper but does not handle
    # as many edge cases.
    #
    @ObjectBase.authorized()
    def do_forced(self, actor, parsed, ctx):

        try:

            custom_verbs = set(ctx.engine.current_custom_verbs(self))

            if parsed.verb in custom_verbs:

                if self.location.process_action(parsed, self):
                    ObjectBase.pending_actions.send(lambda actor=self: actor.location.notify_action(parsed, actor))
                    return
                else:
                    raise ParseError("That action can not be performed in this location's context.")

            if parsed.verb in self.location.exits:
                ctx.engine._go_through_exit(self, parsed.verb)
                return

            action_verbs = set(ctx.engine.current_verbs(self))

            # Sysop actions can be executed by non-Sysops if they are directed to do so by a Sysop
            if parsed.verb in action_verbs:

                func = Actions.get(True)[parsed.verb]

                if getattr(func, "is_generator", False):
                    dialog = func(self, parsed, ctx)
                    # If the action is handled by a generator funciton queue an async dialog
                    ObjectBase.async_dialogs.send((ctx.conn, dialog))
                    return

                func(self, parsed, ctx)
                if func.enable_notify_action:
                    ObjectBase.pending_actions.send(lambda actor=self: actor.location.notify_action(parsed, actor))

                return

            raise ParseError("I do not understand what action you would like the creature to perform.")

        except Exception as x:
            actor.tell("The attempt to force action %s failed." % str(x))


    #
    # Move a craeture from one location to another. This transaction should be atomic: It should either succeed or
    # fail in its entirety. Notices are sent to the actor as well as any creatures in the source and destination
    # locations.
    #
    def move(self, target, actor=None, silent=False, is_player=False, verb="move"):

        actor = actor or self
        original_location = None

        if self.location:

            original_location = self.location
            self.location.remove(self, actor)

            # If the transaction fails roll it back
            try:
                target.insert(self, actor)
            except:
                original_location.insert(self, actor)
                raise

            # Allow for the scneario where a creature silently disappears.
            if not silent:
                original_location.tell("%s leaves." % Lang.capital(self.title), exclude_creature=self)

            if is_player:
                ObjectBase.pending_actions.send(lambda who=self, where=target: original_location.notify_player_left(who, where))
            else:
                ObjectBase.pending_actions.send(lambda who=self, where=target: original_location.notify_npc_left(who, where))

        else:

            target.insert(self, actor)

        if not silent:
            target.tell("%s arrives." % Lang.capital(self.title), exclude_creature=self)

        # queue event
        if is_player:
            ObjectBase.pending_actions.send(lambda who=self, where=original_location: target.notify_player_arrived(who, where))
        else:
            ObjectBase.pending_actions.send(lambda who=self, where=original_location: target.notify_npc_arrived(who, where))


    #
    # Works the same as locate_item but only returns items, not containers.
    #
    def search_item(self, name, include_inventory=True, include_location=True, include_containers=True):

        item, container = self.locate_item(name, include_inventory, include_location, include_containers)

        return item


    #
    # Searches for items within the creature's location around the creature including its inventory.
    # If there is more than one match only the first match is returned. Either returns a  set containing
    # None, None or items, container
    #
    def locate_item(self, name, include_inventory=True, include_location=True, include_containers=True):

        if not name:
            raise ValueError("What item are you trying to locate?")

        found = containing_object = None

        if include_inventory:
            containing_object = self
            found = Creature.search_items(name, self.__inventory)

        if not found and include_location:
            containing_object = self.location
            found = Creature.search_items(name, self.location.items)

        # Search within any containers in the creature's location
        if not found and include_containers:

            for container in self.__inventory:

                containing_object = container

                try:
                    inventory = container.inventory
                # This happens if we do not have access to the container's contents for some reason
                except ActionRefused:
                    continue

                else:

                    found = Creature.search_items(name, inventory)

                    # Once we find a matching item we'll return it to the caller
                    if found:
                        break

        return (found, containing_object) if found else (None, None)



    #
    # Process a custom action against the creature and any items in the creature's inventory.
    # When subclassing Creature override process_action rather than _process_action_base.
    #
    def _process_action_base(self, parsed, actor):

        if self.process_action(parsed, actor):
            return True

        return any(item.process_action(parsed, actor) for item in self.__inventory)


    #
    # Process a custom action. Returns false if nothing resulted.
    #
    def process_action(self, parsed, actor):
        return False


    #
    # Notifies the creature of an action performed by another creature.
    # Also sends the notification to the creature's inventory items.
    #
    def _notify_action_base(self, parsed, actor):

        self.notify_action(parsed, actor)
        for item in self.__inventory:
            item.notify_action(parsed, actor)


    #
    # Override to notify the creature of an action performed by another creature.
    #
    def notify_action(self, parsed, actor):
        pass


    #
    # Override to allow the creature to look around their current location.
    #
    def look(self, short=None):
        pass


    #
    # Search for an item by name within a collection.) in a collection of Items.
    # Returns the first match. Also considers aliases and titles.
    #
    @staticmethod
    def search_items(name, collection):

        name = name.lower()
        items = [i for i in collection if i.name == name]

        # Try all aliases and titles
        if not items:
            items = [i for i in collection if name in i.aliases or i.title.lower() == name]

        return items[0] if items else None