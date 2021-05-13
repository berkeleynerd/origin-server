# coding=utf-8

from origin.common.errors.ActionRefused import ActionRefused
from origin.objects.ObjectBase import ObjectBase


#
# Base class of all Items. Items represent physical objects that can be moved around, used by creatures,
# held in a creature or another item's inventory (containers), etc...
#
class Item(ObjectBase):


    def init(self):

        self.contained_in = None
        self.default_verb = "examine"


    def __contains__(self, item):
        raise ActionRefused("You can not see inside of it.")


    #
    # All locations are either within a location or an item or creature's inventory
    #
    @property
    def location(self):

        if not self.contained_in:
            return None

        from origin.objects.locations.Location import Location

        if isinstance(self.contained_in, Location):
            return self.contained_in

        return self.contained_in.location


    #
    #
    #
    @location.setter
    def location(self, value):

        from origin.objects.locations.Location import Location

        if value is None or isinstance(value, Location):
            self.contained_in = value
        else:
            raise TypeError("You can only use this function to put the item into a location. For containers, use"
                            "the items.contained_in property.")


    @property
    def inventory(self):
        raise ActionRefused("You can not see inside of it.")


    @property
    def inventory_size(self):
        raise ActionRefused("You can not see inside of it.")


    def insert(self, item, actor):
        raise ActionRefused("You can not put anything inside of it.")


    def remove(self, item, actor):
        raise ActionRefused("You can not take anything out of it.")


    #
    # Transactionally move an item from one container to another atomically.
    # By default the move implementation for items is silent for both players and locations.
    #
    def move(self, target, actor=None, silent=False, is_player=False, verb="move"):

        actor = actor or self
        self.allow_item_move(actor, verb)
        source_container = self.contained_in

        if source_container:
            source_container.remove(self, actor)

        try:

            target.insert(self, actor)
            self.notify_moved(source_container, target, actor)

        # If the insert fails put the item back where we found it
        except:

            source_container.insert(self, actor)
            raise


    #
    # Fired when an item has been moved
    #
    def notify_moved(self, source_container, target_container, actor):
        pass

    #
    # Determine whether to allow an item to be moved. Raise an ActionRefused exception to prevent movement.
    #
    def allow_item_move(self, actor, verb="move"):
        pass


    def open(self, actor, item=None):
        raise ActionRefused("You can not open it.")


    def close(self, actor, item=None):
        raise ActionRefused("You can not close it.")


    def lock(self, actor, item=None):
        raise ActionRefused("You can't lock it.")


    def unlock(self, actor, item=None):
        raise ActionRefused("You can't unlock it.")


    @ObjectBase.authorized()
    def sys_clone(self, actor):

        item = ObjectBase.clone(self)
        actor.insert(item, actor)

        actor.tell("Successfully cloned the item into " + repr(item))

        return item


    @ObjectBase.authorized()
    def sys_destroy(self, actor, ctx):

        if self in actor:
            actor.remove(self, actor)
        else:
            actor.location.remove(self, actor)

        self.destroy(ctx)


    #
    # Display the content of the object to the creature
    #
    def show_inventory(self, actor, ctx):

        if self.inventory:

            actor.tell("It appears to contain:")
            for item in self.inventory:
                actor.tell("  " + item.title)

        else:

            actor.tell("It appears to be empty.")