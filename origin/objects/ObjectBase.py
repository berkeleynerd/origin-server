# coding=utf-8

import copy
import functools
import inspect

from textwrap import dedent

from origin import context
from origin.parser import Lang
from origin.engine.pubsub.Topic import Topic
from origin.engine.Context import Context
from origin.common.errors.ActionRefused import ActionRefused


#
# Base class for all in-game objects including items, exits, creatures, and locations
#
# All objects have the following properties:
#
# name              - lowercase name
# title             - shown when location content is displayed
# description       - shown when the object is examined
# short_description - shown when the player uses the look action on their surroundings
# extra_desc        - shown when the player looks specifically based on an arbitrary keyword
#                     useful for allowing the player to explore detail revealed in the description
#                     e.g., the description "Bastet seems to be favoring her left front paw" might
#                     encourage the player to "look at paw" which could reveal more detail.
#
class ObjectBase(object):

    pending_actions = Topic.static_topic("actions")
    pending_tells = Topic.static_topic("tells")
    async_dialogs = Topic.static_topic("dialogs")

    subjective = "it"
    possessive = "its"
    objective = "it"
    gender = "n"


    @property
    def title(self):
        return self._title


    @title.setter
    def title(self, value):
        self._title = value


    @property
    def description(self):
        return self._description


    @description.setter
    def description(self, value):
        self._description = value


    @property
    def short_description(self):
        return self._short_description


    @short_description.setter
    def short_description(self, value):
        self._short_description = value


    @property
    def extra_desc(self):
        return self._extradesc


    @extra_desc.setter
    def extra_desc(self, value):
        self._extradesc = value


    def __init__(self, name, title=None, description=None, short_description=None):

        self.name = None
        self._description = None
        self._title = None
        self._short_description = None

        # Used to map keywords to descriptions to provide additional clues or flavor text
        self._extradesc = {}

        self.init_names(name, title, description, short_description)
        self.aliases = set()

        # Custom actions are registered via a verb-to-docstring mapping.
        # These actions are processed off using a process_action() callback
        self.verbs = {}

        # Set this attribute using the @heartbeat decorator
        if getattr(self, "_register_heartbeat", False):
            self.register_heartbeat()

        self.init()


    #
    # Secondary initialization. Called after required initialization is complete. Override in subclass.
    #
    def init(self):
        pass

    #
    # Set name, title, and related attributes
    #
    def init_names(self, name, title, description, short_description):

        self.name = name.lower()

        if title:
            assert not title.startswith("the ") and not title.startswith("The "), "titles can not begin with 'the'"
            assert not title.startswith("a ") and not title.startswith("A "), "titles can not begin with 'a'"

        self._title = title or name
        self._description = dedent(description).strip() if description else ""
        self._short_description = short_description
        self._extradesc = {}


    #
    # Maps list of keywords to descriptive text
    #
    def add_extradesc(self, keywords, description):
        assert isinstance(keywords, (set, tuple, list))
        for keyword in keywords:
            self._extradesc[keyword] = description


    def __repr__(self):
        return "<%s '%s' @ 0x%x>" % (self.__class__.__name__, self.name, id(self))


    #
    # Basic object cleanup whenever an object is destroyed
    #
    def destroy(self, ctx):
        assert isinstance(ctx, Context)
        self.unregister_heartbeat()
        context.engine.remove_deferreds(self)

    #
    # Allow a Sysop to clone an object
    #
    def sys_clone(self, actor):
        raise ActionRefused(Lang.a(self.__class__.__name__) + " can not be cloned")


    #
    # Allow a Sysop to destroy an object
    #
    def sys_destroy(self, actor, ctx):
        raise ActionRefused(Lang.a(self.__class__.__name__) + " can not be destroyed")


    #
    # Display an object's inventory to the caller
    #
    def show_inventory(self, actor, ctx):
        raise ActionRefused("You can not see inside of that.")


    #
    # Register an object to receive heartbeats. Prefer defereds when possible.
    #
    def register_heartbeat(self):
        context.engine.register_heartbeat(self)


    #
    # Object no longer receive heartbeats.
    def unregister_heartbeat(self):
        context.engine.unregister_heartbeat(self)


    #
    # Only called if the object is registered to receive heartbeats - see register_hearbeat()
    #
    def heartbeat(self, ctx):
        pass

    #
    # Called via the Activate action. Override if the object should respond.
    #
    def activate(self, actor):
        raise ActionRefused("There doesn't seem to be any way to activate it.")


    #
    # Called via the Deactivate action. Override if the object should respond.
    #
    def deactivate(self, actor):
        raise ActionRefused("You can't deactivate that.")


    #
    # Called via the various manipulate actions. Override if the object should respond.
    #
    def manipulate(self, verb, actor):
        raise ActionRefused("You can't seem to %s that or it appears to have no effect." % verb)


    #
    # Move the object to a different location, container, or creature.
    #
    def move(self, target, actor=None, silent=False, is_player=False, verb="move"):
        raise ActionRefused("You can't %s that." % verb)


    #
    # Combine with another object. Override if the object should respond.
    #
    def combine(self, other, actor):
        # combine the other items with us
        raise ActionRefused("You can't seem to combine them.")


    #
    # Read something on or in the object. Override if the object should respond.
    #
    def read(self, actor):
        # called from the read action, override if your object needs to act on this.
        raise ActionRefused("There's nothing there to read.")


    #
    # Deals with custom verbs. Must be overridden.
    # Return true if successful, false if not.
    #
    def process_action(self, parsed, actor):
        return False


    #
    # Notifies an object of an action performed by a creature. Applicable to any verb or action.
    #
    def notify_action(self, parsed, actor):
        pass


    #
    # Generic method to copy an existing object.
    # Does not support objects with an inventory. Override if you need this feature or other custom behvaior.
    #
    @staticmethod
    def clone(obj):

        if isinstance(obj, ObjectBase):

            try:
                if obj.inventory_size > 0:
                    raise ValueError("You can not clone an object that has contents. You need to 'empty' it first.")
            except ActionRefused:
                pass

            # Do not deep copy locations
            if obj.location:
                location, obj.location = obj.location, None
                duplicate = copy.deepcopy(obj)
                obj.location = duplicate.location = location
                return duplicate

        return copy.deepcopy(obj)


    #
    # Decorator indicating that instances of a class should respond to heartbeats.
    # Deferreds are preferrable for performance reasons whereas heartbeats process at
    # least minimally on every tick.
    #
    @staticmethod
    def heartbeat(cls):

        cls._register_heartbeat = True
        return cls


    #
    # Decorator indicating the required actor argument must be a Sysop.
    # If the actor is not a Sysop an ActionRefused error is raised.
    #
    @classmethod
    def authorized(cls):


        def checked(f):

            if "actor" not in inspect.getfullargspec(f).args:
                raise SyntaxError("Function requires an actor as a parameter: " + f.__name__)


            @functools.wraps(f)
            def wrapped(*args, **kwargs):

                # Was an actor supplied?
                actor = inspect.getcallargs(f, *args, **kwargs)["actor"]

                try:
                    if actor and actor.isSysOp:
                        return f(*args, **kwargs)

                # Only Sysops are authorized
                except AttributeError:
                    pass

                raise ActionRefused("You are not allowed to perform that action.")

            return wrapped

        return checked