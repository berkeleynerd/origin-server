# coding=utf-8

#
# Non-Player Character Implementation
#

import random

from origin.parser import Lang

from origin.common.errors.ActionRefused import ActionRefused
from origin.objects.creatures.Creature import Creature


class NPC(Creature):

    def __init__(self, name, gender, title=None, description=None, short_description=None):
        super(NPC, self).__init__(name, gender, title, description, short_description)


    def insert(self, item, actor):

        if actor is self or actor is not None and actor.isSysOp:
            super(NPC, self).insert(item, self)
        else:
            raise ActionRefused("%s does not accept %s." % (Lang.capital(self.title), item.title))


    #
    # A simple implementation of NPC behavior wherein the creature moves about randomly as allowed by exit states.
    # The creature will not move through an exit that leads to a location without exits.
    #
    def select_random_move(self):

        directions_with_exits = [d for d, e in self.location.exits.items() if e.target.exits]

        if directions_with_exits:

            for tries in range(4):

                direction = random.choice(directions_with_exits)
                xt = self.location.exits[direction]

                try:
                    xt.allow_passage(self)
                except ActionRefused:
                    continue
                else:
                    return xt

        return None
