# coding=utf-8

import origin

from origin.objects.creatures.players.Player import Player


class _Gameconfig(object):

    def __init__(self, game):

        config_items = {
            "game",
            "author",
            "version",
            "requires_version",
            "name",
            "gender",
            "server_tick_time",
            "gametime_to_realtime",
            "epoch",
            "player_start",
            "sysop_start",
            "show_exits_in_look",
            "host",
            "port",
            "ssl"
        }

        for attr in config_items:
            setattr(self, attr, getattr(game, attr))


    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class Game:

    game = "ORIGIN"                     # the name of the game
    author = "Anonymous"                # the game's author name
    version = origin.__version__        # arbitrary but is used to check savegames for compatibility
    requires_version = "2.9"            # version required to run the game
    name = "callisti"                   # set a name to create a prebuilt player, None to use the character builder
    gender = "f"                        # m/f/n
    server_tick_time = 5.0              # time between server ticks in seconds
    gametime_to_realtime = 5            # meaning: game time is X times the speed of real time (only used with "timer" tick method) (>=0)
    epoch = None                        # start date/time of the game clock
    player_start = None                 # name of the location where a player starts the game in
    sysop_start = None                  # name of the location where a sysop starts the game in
    show_exits_in_look = True           # show room exits along with room description
    host = "localhost"                  # hostname to bind the server on
    port = 8180                         # port number to bind the server on
    ssl = False                         # Enable / disable SSL support


    #
    # Import any regions that need to be initialized
    #
    def init(self, engine):

        import origin.adventure.regions.convent as convent

        self.player_start = convent.cupola
        self.sysop_start = convent.cupola


    #
    # Called by the game engine when a new player object is created..
    #
    def init_player(self, player):
        pass


    #
    # Welcome the player to the game
    #
    def greet(self, player):
        player.tell("Welcome to '%s'" % self.game)
        player.tell("\n")


    #
    # Say goodbye when the player leaves the game
    #
    def goodbye(self, player: Player):
        player.tell("Please visit again soon.")


    #
    # Handle end of game condition
    #
    def completion(self, player: Player):
        player.tell("Congratulations on finding the ruined foundations!")


    #
    # Create a copy of the game's configuration settings
    #
    def get_config(self):
        return _Gameconfig(self)