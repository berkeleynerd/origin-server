# coding=utf-8

import time
import queue

from threading import Event

from origin.parser import Lang
from origin.common.errors.ActionRefused import ActionRefused

from origin import context

from origin.engine.pubsub.Subscriber import Subscriber
from origin.engine.pubsub.Topic import Topic
from origin.objects.creatures.Creature import Creature
from origin.objects.creatures.players.TextBuffer import TextBuffer


#
# Class representing a player character (PC)
#
class Player(Creature, Subscriber):


    def __init__(self, name, gender, description=None, short_description=None):

        title = Lang.capital(name)

        super(Player, self).__init__(name, gender, title, description, short_description)

        self.turns = 0

        # 0 = off
        # 1 = short descriptions for previously visited locations
        # 2 = short descriptions. for all locations
        self.brief = 0

        self.known_locations = set()
        self.game_complete = False
        self.last_input_time = time.time()
        self.init_nonserializables()


    def init_nonserializables(self):

        self._input = queue.Queue()
        self.input_is_available = Event()
        self._output = TextBuffer()


    def __getstate__(self):

        state = super(Player, self).__getstate__()

        # We don't serialize variables that are either themselves non-serializable
        # or variables that need to be re-initialized.

        # TODO: It's unclear we'll need to serialize given our reliance on database for future game save functionality

        for name in ["_input", "_output", "input_is_available"]:
            del state[name]

        return state


    def __setstate__(self, state):
        super(Player, self).__setstate__(state)
        self.init_nonserializables()


    #
    # When the game is over this will fire.
    #
    def game_completed(self):\
        self.game_complete = True


    #
    # Sends one or more messages to a player via. Output is buffered for efficiency.
    # Empty messages will not be sent. The player object is returned to support call chaining.
    #
    def tell(self, *messages):

        super(Player, self).tell(*messages)

        if messages == ("\n",):
            self._output.new_paragraph()

        msg = " ".join(str(msg) for msg in messages)
        self._output.print(msg)

        return self


    #
    # Responds to a player request to look around their surroundings.
    #
    def look(self, short=None):

        if short is None:

            if self.brief == 2:
                short = True
            elif self.brief == 1:
                short = self.location in self.known_locations

        if self.location:

            self.known_locations.add(self.location)

            # Don't display the player's own description
            look_paragraphs = self.location.look(exclude_creature=self, short=short)

            for paragraph in look_paragraphs:
                self.tell(paragraph)
                self.tell("\n")

        else:
            self.tell("You see nothing at all.")


    #
    # Creature base class processes the move transaction.
    # We set is_player to True to allow it to respond with slightly different behavior in this scenario.
    #
    def move(self, target, actor=None, silent=False, is_player=True, verb="move"):

        # TODO: Should not hard code this. Part of dyna-cide future refactoring effort.
        objectname = target.region + "." + target.varname

        self.saveLocation(self.name, objectname)

        return super(Player, self).move(target, actor, silent, True, verb)


    def saveLocation(self, name, location):

        account = context.engine.accounts.get(name)
        account["location"] = location
        context.engine.accounts.update(account)


    def create_monitor(self, target):
        if not self.isSysOp:
            raise ActionRefused("monitor requires Sysop status")
        tap = target.get_monitor()
        tap.subscribe(self)


    #
    # Report on player activity to any topic subscribers
    #
    def event(self, topicname, event):
        sender, message = event
        self.tell("Monitoring from '%s': %s" % (sender, message))


    #
    # Remove all monitors on the player
    #
    def clear_monitors(self):
        Topic.unsubscribe_all(self)


    def destroy(self, ctx):
        super(Player, self).destroy(ctx)


    #
    # Return all data in the input buffer and clear the input is available flag assuming
    # it will be dealt with and the buffer purged.
    #
    def get_pending_input(self):

        result = []
        self.input_is_available.clear()

        try:
            while True:
                result.append(self._input.get_nowait())
        except queue.Empty:
            return result


    #
    # Add a line of text to the input buffer
    #
    def store_input_line(self, action):

        action = action.strip()
        self._input.put(action)

        self.input_is_available.set()
        self.last_input_time = time.time()


    @property
    def idle_time(self):
        return time.time() - self.last_input_time


    #
    # Search any additional keywords for any location, creature, or item within location around the player. This
    # includes the player's inventory but not the contents of any containers in the room (by default).
    # If there is more than one match we just return the first one we run across.
    #
    def search_extradesc(self, keyword, include_inventory=True, include_containers=False):

        assert keyword
        keyword = keyword.lower()
        desc = self.location.extra_desc.get(keyword)

        if desc:
            return desc

        for item in self.location.items:
            desc = item.extra_desc.get(keyword)
            if desc:
                return desc

        for creature in self.location.creatures:
            desc = creature.extra_desc.get(keyword)
            if desc:
                return desc

        if include_inventory:
            for item in self.inventory:
                desc = item.extra_desc.get(keyword)
                if desc:
                    return desc

        if include_containers:
            for container in self.inventory:
                try:
                    inventory = container.inventory
                # If the container refuses access we'll make no mention of the fact...
                except ActionRefused:
                    continue
                else:

                    for item in inventory:
                        desc = item.extra_desc.get(keyword)
                        if desc:
                            return desc

        return None
