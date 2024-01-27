# coding=utf-8


#
# A new instance of the context class is passed to every action.func and obj.destroy function.
# The player object is not represented because it is passed directly to them as well.
#
class Context(object):


    def __init__(self, engine, clock, config, player_connection):

        self.engine = engine
        self.clock = clock
        self.config = config
        self.conn = player_connection


    def __eq__(self, other):
        return vars(self) == vars(other)