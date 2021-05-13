# coding=utf-8

#
# A timepiece the player can use to track in-game and/or real-time
# e.g., pocket_watch = Clock("clock", title="fine gold pocket watch", short_description="It appears to be ticking.")
#

from origin.parser import Lang

from origin import context
from origin.common.errors.ActionRefused import ActionRefused
from origin.objects.items.Item import Item


class Clock(Item):


    def init(self):

        super(Clock, self).init()
        self.use_locale = True


    @property
    def description(self):

        if self.use_locale:
            display = context.engine.game_clock.clock.strftime("%c")
        else:
            display = context.engine.game_clock.clock.strftime("%Y-%m-%d %H:%M:%S")

        return "It reads " + display


    def activate(self, actor):
        raise ActionRefused("It already appears to be working.")


    def deactivate(self, actor):
        raise ActionRefused("You see know way to turn it off.")


    def manipulate(self, verb, actor):
        actor.tell("%s the %s doesn't seem to have any affect." % (Lang.capital(Lang.progressive_tense(verb)), self.title))


    def read(self, actor):
        actor.tell(self.description)