# coding=utf-8

import re
from collections import defaultdict

from origin.parser import Lang
from origin.common.errors.ParseError import ParseError

from origin.common.errors.NotDefaultVerb import NotDefaultVerb
from origin.parser.ParseResult import ParseResult
from origin.common.errors.UnknownVerbException import UnknownVerbException
from origin.parser.ObjectInfo import ObjectInfo


#
# A parser based on the LPMud parser by Fredrik Hübinette
# Handles high level verb actions and breaking down sentences.
# Verbs specific to a particular game are implemented by modules in the actions package.
#
class Parser(object):

    # Verbs which indicate the player desires to move through an exit
    MOVEMENT_VERBS = {"enter", "climb", "crawl", "go", "run", "move"}

    # Perform a relaxed single or double quoted string match
    _quoted_message_regex = re.compile(r"('(?P<msg1>.*)')|(\"(?P<msg2>.*)\")")

    # Words we can safely ignore when parsing a sentence
    _skip_words = {"and", "&", "at", "to", "before", "in", "into", "on", "off", "onto",
                   "the", "with", "from", "after", "before", "under", "above", "next"}


    def __init__(self):
        self.previously_parsed = None


    #
    # Parse an action string and return the ParseResult object
    #
    def parse(self, player, action, external_verbs=frozenset()):

        # Does the verb expect a message to follow?
        message_verb = False

        # Are we dealing with a custom verb (action)?
        external_verb = False

        message = []
        arg_words = []
        unrecognized_words = []
        obj_info = defaultdict(ObjectInfo)
        obj_order = []
        obj_sequence = 0
        unparsed = action

        # A quoted substring will be considered a message
        m = Parser._quoted_message_regex.search(action)
        if m:
            message = [(m.group("msg1") or m.group("msg2")).strip()]
            action = action[:m.start()] + action[m.end():]

        # Could we determine an action?
        if not action:
            raise ParseError("What?")

        # Ignore skip words
        words = action.split()
        if words and words[0] in Parser._skip_words:
            skipword = words.pop(0)
            unparsed = unparsed[len(skipword):].lstrip()

        # Anything here we understand?
        if not words:
            raise ParseError("What?")

        verb = None

        # Give custom verbs (actions) priority
        if words[0] in external_verbs:
            verb = words.pop(0)
            external_verb = True

        # Let's deal with exits?
        elif player.location.exits:

            # Look for a movement verb
            move_action = None
            if words[0] in Parser.MOVEMENT_VERBS:

                move_action = words.pop(0)

                # If we found a movement verb but no indication of where the player would like to move
                # we'll remind them to supply this bit of information.
                if not words:
                    raise ParseError("%s where?" % Lang.capital(move_action))

            exit, exit_name, wordcount = Parser.check_name_with_spaces(words, 0, player.location.exits, {})

            # Has the user mentioned an exit?
            if exit:

                # If we just have the name of the exit we need to ask the player what they want to do with/about it.
                if wordcount != len(words):
                    raise ParseError("What about it?")

                unparsed = unparsed[len(exit_name):].lstrip()
                raise NotDefaultVerb(ParseResult(verb=exit_name, obj_order=[exit], unparsed=unparsed))

            elif move_action:
                raise ParseError("You can not %s there." % move_action)

            else:
                # can't determine verb at this point, just continue with verb=None
                pass

        else:
            # can't determine verb at this point, just continue with verb=None
            pass

        if verb:
            unparsed = unparsed[len(verb):].lstrip()

        include_flag = True
        collect_message = False

        # Contains all creatures in the location including name and aliases
        all_creatures = {}

        # Contains all items in the location and the player's inventory including name and aliases
        all_items = {}

        # Gather all creatures in the location including the players
        for creature in player.location.creatures:
            all_creatures[creature.name] = creature
            for alias in creature.aliases:
                all_creatures[alias] = creature

        # Gather all items in the location
        for item in player.location.items:
            all_items[item.name] = item
            for alias in item.aliases:
                all_items[alias] = item

        # Gather all items in the player's inventory
        for item in player.inventory:
            all_items[item.name] = item
            for alias in item.aliases:
                all_items[alias] = item

        previous_word = None

        words_enumerator = enumerate(words)
        for index, word in words_enumerator:

            if collect_message:
                message.append(word)
                arg_words.append(word)
                previous_word = word
                continue

            if not message_verb and not collect_message:
                word = word.rstrip(",")

            # Handle special case where player is referring to something using a pronoun.
            # This will work to match a previously parsed word used by the player
            if word in ("them", "him", "her", "it"):

                # Try to associated the pronoun to a previously parsed item or creature
                if self.previously_parsed:

                    obj_list = self.match_previously_parsed(player, word)
                    if obj_list:

                        for obj, name in obj_list:

                            if include_flag:

                                obj_info[obj].sequence = obj_sequence
                                obj_info[obj].previous_word = previous_word
                                obj_sequence += 1
                                obj_order.append(obj)

                            else:

                                del obj_info[obj]
                                obj_order.remove(obj)

                            # If we found a match substitute the name for the pronoun in the list of arguments
                            arg_words.append(name)

                    previous_word = None
                    continue

                # Let the player know we can't figure out what the pronoun is referring to
                raise ParseError("I am not certain to whom you are referring.")

            # Is the player referring to themselves?
            if word in ("me", "myself", "self"):

                if include_flag:

                    obj_info[player].sequence = obj_sequence
                    obj_info[player].previous_word = previous_word
                    obj_sequence += 1
                    obj_order.append(player)

                elif player in obj_info:

                    del obj_info[player]
                    obj_order.remove(player)

                arg_words.append(word)
                previous_word = None
                continue

            # Is the player referring to every creature in the room?
            if word in ("everyone", "everybody", "all"):

                if include_flag:

                    if not all_creatures:
                        raise ParseError("There doesn't appear to be anyone here.")

                    # Include every visible creature and exclude the player
                    for creature in player.location.creatures:
                        if creature is not player:
                            obj_info[creature].sequence = obj_sequence
                            obj_info[creature].previous_word = previous_word
                            obj_sequence += 1
                            obj_order.append(creature)

                else:

                    obj_info = {}
                    obj_order = []
                    obj_sequence = 0

                arg_words.append(word)
                previous_word = None
                continue

            # If the player is trying to refer to all items we tell them we can't handle that
            if word == "everything":
                raise ParseError("You can not do something to everything around you. Please be more specific.")

            # Player wants to exclude an item or creature
            if word in ("except", "but"):
                include_flag = not include_flag
                arg_words.append(word)
                continue

            # Player has referred to a creature?
            if word in all_creatures:

                creature = all_creatures[word]

                if include_flag:

                    obj_info[creature].sequence = obj_sequence
                    obj_info[creature].previous_word = previous_word
                    obj_sequence += 1
                    obj_order.append(creature)

                elif creature in obj_info:

                    del obj_info[creature]
                    obj_order.remove(creature)

                arg_words.append(word)
                previous_word = None
                continue

            # Player has referred to an item?
            if word in all_items:

                item = all_items[word]

                if include_flag:

                    obj_info[item].sequence = obj_sequence
                    obj_info[item].previous_word = previous_word
                    obj_sequence += 1
                    obj_order.append(item)

                elif item in obj_info:

                    del obj_info[item]
                    obj_order.remove(item)

                arg_words.append(word)
                previous_word = None
                continue

            # Just in case the player is not in a location. Not sure how this could happen.
            if player.location:

                exit, exit_name, wordcount = Parser.check_name_with_spaces(words, index, player.location.exits, {})

                # If exits were mentioned let's deal with that
                if exit:

                    obj_info[exit].sequence = obj_sequence
                    obj_info[exit].previous_word = previous_word
                    previous_word = None
                    obj_sequence += 1
                    obj_order.append(exit)
                    arg_words.append(exit_name)

                    while wordcount > 1:
                        Parser.next_iter(words_enumerator)
                        wordcount -= 1

                    continue

            item, full_name, wordcount = Parser.check_name_with_spaces(words, index, all_creatures, all_items)

            # If an item was mentioned then let's deal with that
            if item:

                while wordcount > 1:
                    Parser.next_iter(words_enumerator)
                    wordcount -= 1

                if include_flag:

                    obj_info[item].sequence = obj_sequence
                    obj_info[item].previous_word = previous_word
                    obj_sequence += 1
                    obj_order.append(item)

                elif item in obj_info:

                    del obj_info[item]
                    obj_order.remove(item)

                arg_words.append(full_name)
                previous_word = None
                continue

            # Are we dealing with a message verb?
            if message_verb and not message:
                collect_message = True
                message.append(word)
                arg_words.append(word)
                continue

            # If we are dealing with a word not in skip words list then let's deal with that.
            if word not in Parser._skip_words:

                if not obj_order:

                    for name in all_creatures:

                        if name.startswith(word):
                            raise ParseError("Did you mean %s?" % name)

                    for name in all_items:

                        if name.startswith(word):
                            raise ParseError("Did you mean %s?" % name)

                # If we're not dealing with an external or internal verb we give up
                if not external_verb:

                    # We just have no idea what they hell they're talking about and can't even provide hints.
                    if not verb:
                        raise UnknownVerbException(word, words)

                # If we are dealing with an external verb we'll pass off interpretation to the action modules
                if external_verb:
                    arg_words.append(word)
                    unrecognized_words.append(word)

                # Otherwise we're again at the end of our rope
                else:

                    message = "I am not sure what you mean by '%s'." % word

                    if word[0].isupper():
                        message += " Please always just user lowercase (e.g., '%s')." % word.lower()

                    raise ParseError(message)

            previous_word = word


        message = " ".join(message)

        # There appears to be no verb but it's possible the user is referring to an item or creature.
        # In that case we can check the object or creature to determine a default verb to apply.
        if not verb:

            if len(obj_order) == 1:

                try:

                    verb = obj_order[0].default_verb

                # Our last resort is to use the "examine" action to provide detailed information on the object
                except AttributeError:
                    verb = "examine"

            else:

                raise UnknownVerbException(words[0], words)

        # We're done parsing. Let's pass a parse result object back to the caller so that the various action
        # modules have a chance to pick the sentence apart and respond appropriately.
        return ParseResult(verb, obj_info=obj_info, obj_order=obj_order,
                           message=message, args=arg_words, unrecognized=unrecognized_words, unparsed=unparsed)


    #
    # Try to match a pronoun (it, him, her, them) to a previously parsed item or creature.
    # Returns a list of (object, proper-name) tuples. Helps make parsing and other processing consistent.
    #
    def match_previously_parsed(self, player, pronoun):

        # Plural that can match any items or creatures
        if pronoun == "them":

            matches = list(self.previously_parsed.obj_order)

            for obj in matches:

                if not player.search_item(obj.name) and obj not in player.location.creatures:
                    player.tell("(By '%s' I assume you mean %s.)" % (pronoun, obj.title))
                    raise ParseError("%s is no longer nearby." % Lang.capital(obj.subjective))

            if matches:

                player.tell("(By '%s' I assume you mean %s.)" % (pronoun, Lang.join(who.title for who in matches)))
                return [(who, who.name) for who in matches]

            else:

                raise ParseError("It is not clear to whom you are referring.")

        for obj in self.previously_parsed.obj_order:

            # Are we dealing with an exit?
            if pronoun == "it":

                for direction, exit in player.location.exits.items():

                    if exit is obj:
                        player.tell("(By '%s' I assume you mean '%s'.)" % (pronoun, direction))
                        return [(obj, direction)]

            # If not, are we dealing with an item or creature?
            if pronoun == obj.objective:

                if player.search_item(obj.name) or obj in player.location.creatures:
                    player.tell("(By '%s' I assume you mean %s.)" % (pronoun, obj.title))
                    return [(obj, obj.name)]

                player.tell("(By '%s' I assume you mean %s.)" % (pronoun, obj.title))

                raise ParseError("%s is no longer nearby." % Lang.capital(obj.subjective))

        raise ParseError("It is not clear who you're referring to.")


    @staticmethod
    def check_name_with_spaces(words, index, all_creatures, all_items):

        wordcount = 1
        name = words[index]

        try:

            # Limit the number of words we're willing to concatenate
            while wordcount < 6:

                if name in all_creatures:
                    return all_creatures[name], name, wordcount

                if name in all_items:
                    return all_items[name], name, wordcount

                name = name + " " + words[index + wordcount]
                wordcount += 1

        except IndexError:
            pass

        return None, None, 0


    @staticmethod
    def next_iter(iterable):
        return next(iterable)