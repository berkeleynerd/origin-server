# coding=utf-8

from origin.common.errors.LocationIntegrityError import LocationIntegrityError
from origin.objects.items.Item import Item


#
# Represents a key which which can be used to unlock a door or container that matches code.
#
class Key(Item):

    def init(self):

        super(Key, self).init()
        self.code = None


    #
    # Create a key matching the specified door
    #
    def doorKey(self, door=None, code=None):

        if code:
            assert door is None
            self.code = code
        else:
            self.code = door.code
            if not self.code:
                raise LocationIntegrityError("The door specified has code value.", None, door, door.target)