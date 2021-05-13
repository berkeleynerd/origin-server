# coding=utf-8

import sys

from origin.actions.Actions import Actions
from origin.common.errors.ActionRefused import ActionRefused


#
# Reload the specified Python module.
#
class Reload(Actions):

    @staticmethod
    @Actions.action("reload")
    @Actions.sysop
    def func(player, parsed, ctx):

        if not parsed.args:
            raise ActionRefused("Which module would you like to reload?")

        path = parsed.args[0]
        if not path.startswith("."):
            raise ActionRefused("A valid module path must begin with '.'")

        try:

            module_name = "origin.adventure.regions"
            if len(path) > 1:
                module_name += path
            __import__(module_name)
            module = sys.modules[module_name]

        except (ImportError, ValueError):

            raise ActionRefused("I can't find a module named " + path)

        import importlib
        importlib.reload(module)
        player.tell("The module %s has been reloaded." % module.__name__)