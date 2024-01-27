# coding=utf-8

import textwrap

from origin.objects.items.Item import Item


#
# A piece of paper, possibly with something written on it the player can read.
#
# e.g., newspaper = Note("shopping list", description="Looks to be a shopping list")
#       newspaper.text = "Tooth Brush", "Tooth Paste", "Dental Floss"
#       newspaper.aliases.add("note")
#


class Note(Item):

    def init(self):

        super(Note, self).init()
        self._text = "There doesn't appear to be anything written on it."


    @property
    def text(self):
        return self._text


    @text.setter
    def text(self, text):
        self._text = textwrap.dedent(text)


    def read(self, actor):
        actor.tell("The %s reads:" % self.title)
        actor.tell(self.text)