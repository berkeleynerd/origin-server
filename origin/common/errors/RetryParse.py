# coding=utf-8

#
# Allows actions to forward handling to other actions
#
class RetryParse(Exception):

    def __init__(self, action):

        self.action = action