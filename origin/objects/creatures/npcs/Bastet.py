# coding=utf-8

import random

from origin import context
from origin.parser.Lang import capital
from origin.objects.creatures.npcs.OriginNPC import OriginNPC


class Bastet(OriginNPC):


    def init(self):

        self.following = None
        self.aliases = {"cat"}
        context.engine.defer(256, self.do_purr)
        context.engine.defer(random.randint(20, 60), self.do_wander)


    #
    # Serval cats (which is what Bastet is) can also make high-pitched chirps, hisses,
    # crackles, growls, and grunts along with the more typcial 'meow'
    #
    def do_purr(self, ctx):

        if random.random() > 0.5:
            self.location.tell("%s chirps happily." % capital(self.title))
        else:
            self.location.tell("%s yawns and licks her paws." % capital(self.title))

        ctx.engine.defer(random.randint(5, 256), self.do_purr)


    #
    # Bastet likes to wander around until she finds the last person who gave her some affection.
    #
    def do_wander(self, ctx):

        if self.following is not None:
            destination = self.following.location.name
        else:
            destination = None

        if self.location.name != destination:

            direction = self.select_random_move()
            if direction:
                self.move(direction.target, self)

        ctx.engine.defer(random.randint(20, 60), self.do_wander)


    def notify_action(self, parsed, actor):

        if self.name in parsed.args:

            if parsed.verb in ("pet", "stroke", "tickle", "cuddle", "hug"):

                self.tell_others("{Title} gingerly stretches, paws around until she's snug, and starts to purr "
                                 "contentedly.")
                self.following = actor

            elif parsed.verb in ("hello", "hi", "greet"):

                self.tell_others("{Title} blinks and gives you a quizzical look.")

            else:

                message = (parsed.message or parsed.unparsed).lower()
                if self.name in message:
                    self.tell_others("{Title} glances at your briefly.")