# coding=utf-8

import datetime
import inspect
import sys
from functools import total_ordering

import types


#
# An action that will be invoked in the future. Only serializable objects are candidates.
#
@total_ordering
class Deferred(object):


    def __init__(self, due, action, vargs, kwargs):

        assert due is None or isinstance(due, datetime.datetime)
        assert callable(action) # Deferreds must be __call__-able

        # As game-time
        self.due = due

        self.owner = getattr(action, "__self__", None)

        # Use module's name to encode
        if isinstance(self.owner, types.ModuleType):
            self.owner = "module:" + self.owner.__name__

        # Work a little harder to get that module name...
        if self.owner is None:

            action_module = getattr(action, "__module__", None)

            if action_module:

                if hasattr(sys.modules[action_module], action.__name__):
                    self.owner = "module:" + action_module

                # A callable was passed that we cannot serialize.
                else:
                    raise ValueError("We can't use scoped functions or lambdas as deferreds because"
                                     "we can't serialize them : " + str(action))

            else:

                raise ValueError("We can't determine action's owner : " + str(action))

        # We store the name rather than the object to support serialization
        self.action = action.__name__
        self.vargs = vargs
        self.kwargs = kwargs


    def __eq__(self, other):

        return self.due == other.due and type(self.owner) == type(other.owner)\
            and self.action == other.action and self.vargs == other.vargs and self.kwargs == other.kwargs

    def __lt__(self, other):

        # Deferreds must be sortable.
        return self.due < other.due


    #
    # Sets the countdown timer for deferred's processing.
    # Defaults to game-time.
    #
    def when_due(self, game_clock, realtime=False):

        secs = (self.due - game_clock.clock).total_seconds()

        if realtime:
            secs = int(secs / game_clock.multiplier)

        return datetime.timedelta(seconds=secs)


    def __call__(self, *args, **kwargs):

        self.kwargs = self.kwargs or {}

        if callable(self.action):
            func = self.action


        # The deferred action is stored as the name of the function to call so we need to retrieve the actual
        # function from the containing object.
        else:

            if isinstance(self.owner, str):

                # The containing object refers to a module?
                if self.owner.startswith("module:"):
                    self.owner = sys.modules[self.owner[7:]]

                else:
                    raise RuntimeError("An invalid containing object was specified: " + self.owner)

            func = getattr(self.owner, self.action)

        if "ctx" in inspect.getargspec(func).args:
            self.kwargs["ctx"] = kwargs["ctx"]  # add a 'ctx' keyword argument to the call for convenience

        func(*self.vargs, **self.kwargs)

        # Object's life is over. Let's cleanup.

        del self.owner
        del self.action
        del self.kwargs
        del self.vargs
