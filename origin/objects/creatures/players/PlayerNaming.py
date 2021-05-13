# coding=utf-8


class PlayerNaming(object):


    def __init__(self):
        self._name = self.title = self.gender = self.description = None


    def apply_to(self, player):
        assert self._name
        assert self.gender
        player.init_gender(self.gender)
        player.init_names(self._name, self.title, self.description, None)


    @property
    def name(self):
        return self._name


    @name.setter
    def name(self, value):
        self._name = value.lower()