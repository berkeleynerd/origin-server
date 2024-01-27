# coding=utf-8

from origin.objects.locations.Location import Location


#
# Handle game ending based on player accessing a particular location.
#
class GameEnd(Location):
    def init(self):
        pass

    def notify_player_arrived(self, player, previous_location):
        print("PLAYER HAS WON!")
        player.game_completed()