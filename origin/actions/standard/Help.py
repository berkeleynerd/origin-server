# coding=utf-8

from origin.actions.Actions import Actions
from origin.actions.standard import What


#
# Help the player understand basic game mechanics
#
class Help(Actions):

    @staticmethod
    @Actions.action("help")
    @Actions.disable_notify
    def func(player, parsed, ctx):

        # Sysops get more detailed information
        if player.isSysOp:
            if parsed.args:
                What.what(player, parsed, ctx)
            else:
                all_verbs = ctx.engine.current_verbs(player)
                verb_help = {}

                for verb in all_verbs:
                    verb_help[verb] = []

                actions_help = []
                for verb, abbreviations in verb_help.items():
                    if abbreviations:
                        verb += "/" + "/".join(abbreviations)
                    actions_help.append(verb)

                player.tell("I understand the following vocabulary related to actions I can perform:")
                player.tell(", ".join(sorted(actions_help)))
                player.tell("\n")

        else:
            help = (
            "I know of places, actions, items, and creatures. Most of my vocabulary describes places and is used to"
            " move you there. To move about, try to say things like 'go door', 'go stairwell', north, south, northeast,"
            " or down. I know about a few special"
            " items and creatures like Bastet, a friendly cat who wanders the game. If you 'pet bastet' she'll follow"
            " you around if she's able. Many items can be manipulated using the action words I know. Usually you will"
            " need to specify both the action and an items, location, or creature like 'get keys' or 'unlock door'. Some"
            " objects simply imply actions; in particular, 'inventory' implies 'take' inventory,' which causes me to"
            " give you a list of what you're carrying. Items usually have useful side effects; for instance, Bastet"
            " scares rats away. If you're having trouble moving about just try a few different words.  If you're trying"
            " unsuccessfully to manipulate an object you are probably attempting something beyond my capability to"
            " understand and you should try a completely different approach.")

            player.tell(help)
