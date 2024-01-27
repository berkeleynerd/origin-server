# coding=utf-8

import random

from origin.objects.creatures.npcs.Npc import NPC


#
# Generic NPC behavior tailored to the Origin game universe
#
class OriginNPC(NPC):


    def init(self):

        super(OriginNPC, self).init()


    def do_wander(self, ctx):

        direction = self.select_random_move()

        if direction:
            self.move(direction.target, self)

        ctx.engine.defer(random.randint(20, 60), self.do_wander)