# coding=utf-8

#
# Occurs when the engine finds a problem with a location or exit or the bindings between them
#
class LocationIntegrityError(Exception):

    def __init__(self, msg, direction, exit, location):

        super(LocationIntegrityError, self).__init__(msg)
        self.direction = direction
        self.exit = exit
        self.location = location