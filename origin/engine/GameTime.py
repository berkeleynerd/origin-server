# coding=utf-8

#
# Various utility functions
#

import datetime

#
# Track time within the game world.
# The multiplier parameter determines the game time to real time ratio
# The clock value tracks game time
#
class GameTime(object):


    def __init__(self, date_time, multiplier=1):

        assert multiplier >= 0
        self.multiplier = multiplier
        self.clock = date_time


    def __str__(self):
        return str(self.clock)


    #
    # Advance game clock by time delta expressed as game time
    #
    def add_gametime(self, timedelta):

        assert isinstance(timedelta, datetime.timedelta)
        self.clock += timedelta


    #
    # Report game clock plus a time delta expressed as real time
    #
    def plus_realtime(self, timedelta):

        assert isinstance(timedelta, datetime.timedelta)
        return self.clock + timedelta * self.multiplier


    #
    # Advance game clock by time delta expressed as real time
    #
    def add_realtime(self, timedelta):

        assert isinstance(timedelta, datetime.timedelta)
        self.clock += timedelta * self.multiplier

