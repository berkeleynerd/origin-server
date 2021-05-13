# coding=utf-8


from origin.actions.Actions import Actions
from origin.common.errors.ActionRefused import ActionRefused
from origin.common.errors.ParseError import ParseError
from origin.objects.creatures.Creature import Creature
from origin.objects.creatures.players.Player import Player
from origin.common.errors.NotDefaultVerb import NotDefaultVerb


#
# Force another creature into performing the specified action.
#
class Force(Actions):

    @staticmethod
    @Actions.action("force", "coerce", "compel")
    @Actions.sysop
    def func(player, parsed, ctx):

        if len(parsed.args) < 2 or not parsed.obj_order:
            raise ParseError("Who would you like to force to do what?")

        target = parsed.obj_order[0]
        if not isinstance(target, Creature):
            raise ActionRefused("You cannot force inanimate objects to perform an action.")

        action = parsed.args[1]

        # Make sure we know the action in question
        if action not in ctx.engine.current_verbs(target) and action not in target.location.exits:
            raise ParseError("I don't understand the word '%s'." % action)

        action = parsed.unparsed.partition(action)
        action = action[1] + action[2]

        target.tell("An unseen force compels you...")
        player.tell("You force <player>%s</player> into performing an action." % target.title)

        # If target is another player then record the action in the player's input buffer
        if isinstance(target, Player):
            target.store_input_line(action)
            return

        # Now perform the action on behalf of the target, from the viewpoint of the current player!

        custom_verbs = set(ctx.engine.current_custom_verbs(target))
        action_verbs = set(ctx.engine.current_verbs(target))
        all_verbs = custom_verbs | action_verbs

        try:
            target_parsed = target.parse(action, all_verbs)
            raise ParseError("Unknown action specified.")
        except NotDefaultVerb as x:
            # if not a default verb try to find the associated action
            target.do_forced(player, x.parsed, ctx)