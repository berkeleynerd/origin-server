# coding=utf-8

from origin.parser import Lang

from origin.common.errors.ActionRefused import ActionRefused
from origin.common.errors.LocationIntegrityError import LocationIntegrityError
from origin.objects.exits.Exit import Exit


#
# A door is an exit that connects one location to another but which can be opened, closed, locked, and unlocked.
#
class Door(Exit):

    def __init__(self, directions, target_location, short_description, long_description=None, locked=False, opened=True):

        self.locked = locked
        self.opened = opened

        # Long description will default to short description if not long_description is provided

        self.__description_prefix = long_description or short_description

        # Allow for codes that match keys to doors they can unlock
        self.code = None

        super(Door, self).__init__(directions, target_location, short_description, long_description)

        if locked and opened:
            raise ValueError("A door cannot be both locked and open.")

        self.linked_door = None


    class DoorPairLink(object):
        def __init__(self, other_door, other_open_msg=None, other_close_msg=None):
            self.door = other_door
            self.open_msg = other_open_msg
            self.close_msg = other_close_msg


    #
    # Returns a new Door object in the connected location linked to this one such that their open and lock state
    # will always match.
    #
    def reverse_door(self, directions, returning_location, short_description, long_description=None,
                     reverse_open_msg=None, reverse_close_msg=None, this_open_msg=None, this_close_msg=None):

        other_door = Door(directions, returning_location, short_description, long_description,
                          locked=self.locked, opened=self.opened)
        self.linked_door = Door.DoorPairLink(other_door, this_open_msg, this_close_msg)
        other_door.linked_door = Door.DoorPairLink(self, reverse_open_msg, reverse_close_msg)
        other_door.code = self.code

        return other_door


    @property
    def description(self):

        if self.opened:
            status = "It is open "
        else:
            status = "It is closed "
        if self.locked:
            status += "and locked."
        else:
            status += "and unlocked."

        return self.__description_prefix + " " + status


    def __repr__(self):
        target = self.target.name if self.bound else self.target
        locked = "locked" if self.locked else "open"
        return "<base.Door '%s'->'%s' (%s) @ 0x%x>" % (self.name, target, locked, id(self))


    #
    # Is the creature allowed to move through this door?
    #
    def allow_passage(self, actor):

        if not self.bound:
            raise LocationIntegrityError("This door appears to be stuck shut.", None, self, None)

        if not self.opened:
            raise ActionRefused("The door is closed.")


    #
    # Open the door, optionally using an an item. E.g., a key.
    # Also notified creatures in the room about Door object state changes.
    #
    def open(self, actor, item=None):

        if self.opened:
            raise ActionRefused("It is already open.")

        elif self.locked:
            raise ActionRefused("It is locked.")

        else:
            self.opened = True
            actor.tell("You open it.")
            actor.tell_others("{Title} opens the %s." % self.name)

            if self.linked_door:
                self.linked_door.door.opened = True
                if self.linked_door.open_msg:
                    self.target.tell(self.linked_door.open_msg)


    #
    # Close the door, optionally using an an item. E.g., a key.
    # Also notified creatures in the room about Door object state changes.
    #
    def close(self, actor, item=None):

        if not self.opened:
            raise ActionRefused("It is already closed.")

        self.opened = False
        actor.tell("You close it.")
        actor.tell_others("{Title} closes the %s." % self.name)

        if self.linked_door:
            self.linked_door.door.opened = False
            if self.linked_door.close_msg:
                self.target.tell(self.linked_door.close_msg)


    #
    # Lock the door with the matching key(s)
    #
    def lock(self, actor, item=None):

        if self.locked:
            raise ActionRefused("It is already locked.")

        if item:

            if self.check_key(item):
                key = item
            else:
                raise ActionRefused("That can not be used to lock it.")

        else:

            key = self.search_key(actor)
            if not key:
                raise ActionRefused("You don't seem to have the key necessary to lock it.")

        self.locked = True
        actor.tell("You lock the %s with %s." % (self.name, Lang.a(key.title)))
        actor.tell_others("{Title} locked the %s with %s." % (self.name, Lang.a(key.title)))

        if self.linked_door:
            self.linked_door.door.locked = True



    #
    # Unlock the door with the matching key(s)
    def unlock(self, actor, item=None):

        if not self.locked:
            raise ActionRefused("It is not locked.")

        if item:

            if self.check_key(item):
                key = item
            else:
                raise ActionRefused("You can't use that to unlock it.")

        else:

            key = self.search_key(actor)
            if not key:
                raise ActionRefused("You don't seem to have the key necessary to unlock it.")

        self.locked = False
        actor.tell("You unlock the %s with %s." % (self.name, Lang.a(key.title)))
        actor.tell_others("{Title} unlocked the %s with %s." % (self.name, Lang.a(key.title)))

        if self.linked_door:
            self.linked_door.door.locked = False


    #
    # Check if the player's inventory contains the key with the proper code to open this door.
    #
    def check_key(self, item):

        code = getattr(item, "code", None)

        # If this door is linked to another the code we need may have been set on it instead.
        if self.linked_door:

            other_code = self.linked_door.door.code
            if self.code is None:
                self.code = other_code
            else:
                assert self.code == other_code, "The linked doors have keys that do not match."

        return code and code == self.code


    #
    # Does the player have the correct key in their inventory? If so return the item.
    #
    def search_key(self, actor):

        for item in actor.inventory:
            if self.check_key(item):
                return item

        return None


    #
    # Handles the case where the player tried to put the key into the door. Sensible to do but not how it works
    # in our game.
    #
    def insert(self, item, actor):

        if self.check_key(item):
            if self.locked:
                raise ActionRefused("You should try to unlock the door with it instead.")
            else:
                raise ActionRefused("You should try to lock the door with it instead.")

        raise ActionRefused("The %s doesn't seem to fit." % item.title)