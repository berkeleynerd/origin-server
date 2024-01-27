# coding=utf-8

import inspect

from origin.common.errors.ActionRefused import ActionRefused
from origin.parser import Lang


#
# Basic functionality to deal with actions. We're using verb and action fairly interchangeably as the
# parser code was ported from LPMud's C based parser
#
class Actions(object):


    actions_by_privelege = {None: {}}


    def __init_subclass__(cls, **kwargs):

        for alias in cls.func.aliases:
            if hasattr(cls.func, "isSysopFunction"):
                Actions.actions_by_privelege.setdefault("sysop", {})[alias] = cls.func
            else:
                Actions.actions_by_privelege.setdefault(None, {})[alias] = cls.func


    @staticmethod
    def add(verb, func, privilege=None):
        Actions.validateFunc(func)
        for actions in Actions.actions_by_privelege.values():
            if verb in actions:
                raise ValueError("action defined more than once: " + verb)
        Actions.actions_by_privelege.setdefault(privilege, {})[verb] = func


    @staticmethod
    def get(isSysOp):
        result = dict(Actions.actions_by_privelege[None])  # always include the actions for None
        if isSysOp:
            result.update(Actions.actions_by_privelege["sysop"])
        return result


    @staticmethod
    def validateFunc(func):
        if not hasattr(func, "is_action_func"):
            raise ValueError("the function '%s' is not a proper action function (did you forget the decorator?)" % func.__name__)


    # decorator preventing an action from creature passed to notify_action
    @classmethod
    def disable_notify(cls, func):
        func.enable_notify_action = False
        return func

    # decorator preventing an action from creature passed to notify_action
    @classmethod
    def sysop(cls, func):
        func.isSysopFunction = True
        return func


    #  decorator enabling an action to override a parser verb
    @classmethod
    def override_parser(cls, func):
        func.overrides_parser = True
        return func


    # decorator instructing parser to ignore input and allow it to be treated as pure text
    @classmethod
    def no_parser(cls, func):
        func.no_parser = True
        return func


    @classmethod
    def parse_is_are(cls, args):
        if args:
            if args[0] == "are":
                raise ActionRefused("Be more specific.")
            elif args[0] == "is":
                if len(args) >= 2:
                    del args[0]  # skip 'is', but only if more args follow
                else:
                    raise ActionRefused("Who do you mean?")


    # decorator specifying aliases of an action
    @classmethod
    def action(cls, action, *aliases):

        # TODO: We need to document why this inner function is necessary...
        def action_extend(func):

            # Does this function contain an async yield?
            # This happens, for example, when we're prompting a user for input
            func.is_generator = inspect.isgeneratorfunction(func)

            if not hasattr(func, "enable_notify_action"):
                func.enable_notify_action = True

            func.aliases = [action]
            func.aliases.extend(aliases)
            return func

        return action_extend


    @staticmethod
    def print_object_location(player, obj, container, print_parentheses=True):

        if not container:

            if print_parentheses:
                player.tell("(I am not sure where %s is)" % obj.name)
            else:
                player.tell("I am not sure where %s is." % obj.name)
            return

        if container in player:

            if print_parentheses:
                player.tell("(You are carrying %s.)" % obj.name)
            else:
                player.tell("You are carrying %s." % Lang.capital(obj.name))

        elif container is player.location:

            if print_parentheses:
                player.tell("(%s is here with you.)" % obj.name)
            else:
                player.tell("%s is here with you." % Lang.capital(obj.name))

        elif container is player:

            if print_parentheses:
                player.tell("(You are carrying %s)" % obj.name)
            else:
                player.tell("You are carrying %s" % Lang.capital(obj.name))

        else:

            if print_parentheses:
                player.tell("(%s was located in %s)." % (obj.name, container.name))
            else:
                player.tell("%s was located in %s." % (Lang.capital(obj.name), container.name))