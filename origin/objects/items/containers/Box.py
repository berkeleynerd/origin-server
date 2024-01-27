# coding=utf-8

from origin.common.errors.ActionRefused import ActionRefused
from origin.objects.items.containers.Container import Container


#
# A container sub-base that can open and close and supports additiona descriptive attributes.
# e.g., chest = Box("chest", "heavy jade chest")
#
class Box(Container):


    def init(self):

        super(Box, self).init()

        self.opened = False
        self.txt_title_closed = self._title
        self.txt_title_open_filled = "filled " + self._title
        self.txt_title_open_empty = "empty " + self._title
        self.txt_descr_closed = "The lid is closed."
        self.txt_descr_open_filled = "It is a %s. The lid is open and there appears to be something in it." % self.name
        self.txt_descr_open_empty = "It is a %s with an open lid." % self.name


    def allow_item_move(self, actor, verb="move"):
        raise ActionRefused("You can not %s %s." % (verb, self.title))


    @property
    def title(self):

        if self.opened:
            return self.txt_title_open_filled if self.inventory_size else self.txt_title_open_empty
        else:
            return self.txt_title_closed


    @property
    def description(self):

        if self.opened:
            if self.inventory_size:
                return self.txt_descr_open_filled
            else:
                return self.txt_descr_open_empty
        else:
            return self.txt_descr_closed


    def open(self, actor, item=None):

        if self.opened:
            raise ActionRefused("It is already open.")

        self.opened = True

        actor.tell("You open the %s." % self.name)
        actor.tell_others("{Title} opens the %s." % self.name)


    def close(self, actor, item=None):

        if not self.opened:
            raise ActionRefused("It is already closed.")

        self.opened = False

        actor.tell("You close the %s." % self.name)
        actor.tell_others("{Title} closes the %s." % self.name)


    @property
    def inventory(self):

        if self.opened:
            return super(Box, self).inventory
        else:
            raise ActionRefused("You'll need to open it to see what's inside...")


    @property
    def inventory_size(self):

        if self.opened:
            return super(Box, self).inventory_size
        else:
            raise ActionRefused("You'll need to open it to see what's inside...")


    def insert(self, item, actor):

        if self.opened:
            super(Box, self).insert(item, actor)
        else:
            raise ActionRefused("It's closed. You'll need to open it first...")


    def remove(self, item, actor):

        if self.opened:
            super(Box, self).remove(item, actor)
        else:
            raise ActionRefused("It's closed. You'll need to open it first...")
