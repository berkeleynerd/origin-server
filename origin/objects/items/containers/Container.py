# coding=utf-8

from origin.objects.ObjectBase import ObjectBase
from origin.objects.items.Item import Item


#
# An item that can contain other items.
# Supports the "in" operator to check for particular items in the container.
# Primary functions are insert and remove.
#
class Container(Item):


    def init(self):
        super(Container, self).init()
        self.__inventory = set()


    #
    # Initialize container inventory
    #
    def init_inventory(self, items):

        assert len(self.__inventory) == 0

        self.__inventory = set(items)

        for item in items:
            item.contained_in = self


    @property
    def inventory(self):
        return frozenset(self.__inventory)


    @property
    def inventory_size(self):
        return len(self.__inventory)


    def __contains__(self, item):
        return item in self.__inventory


    def destroy(self, ctx):

        super(Container, self).destroy(ctx)

        for item in self.__inventory:
            item.destroy(ctx)

        self.__inventory.clear()


    def insert(self, item, actor):

        assert isinstance(item, ObjectBase)

        self.__inventory.add(item)
        item.contained_in = self

        return self


    def remove(self, item, actor):

        self.__inventory.remove(item)
        item.contained_in = None

        return self