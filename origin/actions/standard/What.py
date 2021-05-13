# coding=utf-8

from origin.parser import Lang

from origin.actions.Actions import Actions
from origin.common.errors.ParseError import ParseError
from origin.common.errors.ActionRefused import ActionRefused


#
# Tries to explain an action, exit, creature, or item.
#
class What(Actions):

    @staticmethod
    @Actions.action("what")
    @Actions.disable_notify
    def func(player, parsed, ctx):

        if not parsed.args:
            raise ParseError("What are you asking about?")

        if parsed.args[0] == "are" and len(parsed.args) > 2:
            raise ActionRefused("I can only tell you about one thing at a time.")

        if len(parsed.args) >= 2 and parsed.args[0] in ("is", "are"):
            del parsed.args[0]

        name = parsed.args[0].rstrip("?")

        if not name:
            raise ActionRefused("What are you asking about?")

        found = False

        # Is the player asking about an action?
        all_verbs = ctx.engine.current_verbs(player)
        if name in all_verbs:
            found = True
            doc = all_verbs[name].strip()

            if doc:
                player.tell(doc)
            else:
                player.tell("That is an action I understand but I can't tell you much more about it.")

        # Is the player asking about a particular exit from their current location?
        if name in player.location.exits:
            found = True
            player.tell("That appears to be a way to leave your current location. Perhaps you should examine it?")

        # Is the player asking about a creature in the room with them?
        creature = player.location.search_creature(name)
        if creature and creature.name.lower() != name.lower() and name.lower() in creature.aliases:
            player.tell("(By %s you probably meant %s.)" % (name, creature.name))

        if creature:
            found = True

            # Is the player referring to themselves here?
            if creature is player:
                player.tell("Well, that's you isn't it?")

            # Or are they referring to someone else in the room?
            else:
                title = Lang.capital(creature.title)
                gender = Lang.GENDERS[creature.gender]
                subj = Lang.capital(creature.subjective)

                if type(creature) is type(player):
                    player.tell("Is another visitor like yourself. %s's here in the room with you." % subj)
                else:
                    player.tell("<creature>%s</creature> is a %s character in our story." % (title, gender))

        # Is the player referring to an item?
        item, container = player.locate_item(name, include_inventory=True, include_location=True, include_containers=True)
        if item:
            found = True
            if item.name.lower() != name.lower() and name.lower() in item.aliases:
                player.tell("Maybe you meant %s.)" % item.name)
            player.tell("That's a nearby item you could try to examine for more information.")

        if name in ("that", "this", "they", "them", "it"):
            raise ActionRefused("Sorry, you need to be more specific.")

        # Shrug our virtual shoulders...
        if not found:
            player.tell("Sorry, I can't figure out what you mean or there is no additional information I can provide.")
